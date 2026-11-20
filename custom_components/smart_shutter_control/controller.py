"""One shutter: decides with the rule chain, limits, calibrates and moves through the adapter."""

from __future__ import annotations

from homeassistant.config_entries import ConfigSubentry
from homeassistant.core import HomeAssistant

from .adapter import CoverAdapter
from .const import (
    CONF_AZIMUTH,
    CONF_CALIBRATION,
    CONF_COVER,
    CONF_MAX_ELEVATION,
    CONF_MAX_POSITION,
    CONF_MIN_ELEVATION,
    CONF_ROOM_TEMPERATURE,
    CONF_TILT,
    DEFAULT_SHUTTER,
)
from .core.calibration import Calibration, DirectionTracker, RollerCalibration
from .core.limits import PositionLimiter
from .core.model import Decision, Direction, Inputs, Reason, ShutterConfig, ShutterContext
from .core.rules import RuleChain
from .storage import RuntimeStore

KEY_AUTOMATIC = "automatic"
KEY_MAX_POSITION = "max_position"


def shutter_config(data: dict) -> ShutterConfig:
    values = {**DEFAULT_SHUTTER, **data}
    return ShutterConfig(
        cover=values[CONF_COVER],
        azimuth=float(values[CONF_AZIMUTH]),
        tilt=float(values[CONF_TILT]),
        min_elevation=float(values[CONF_MIN_ELEVATION]),
        max_elevation=float(values[CONF_MAX_ELEVATION]),
        room_temperature=values.get(CONF_ROOM_TEMPERATURE),
    )


class ShutterController:
    def __init__(
        self,
        hass: HomeAssistant,
        subentry: ConfigSubentry,
        store: RuntimeStore,
        chain: RuleChain | None = None,
        calibration: Calibration | None = None,
    ) -> None:
        self.id = subentry.subentry_id
        self.title = subentry.title
        self.subentry_data = dict(subentry.data)
        self.config = shutter_config(dict(subentry.data))
        self.default_max = int(subentry.data.get(CONF_MAX_POSITION, DEFAULT_SHUTTER[CONF_MAX_POSITION]))
        self.store = store
        self.chain = chain or RuleChain()
        self.limiter = PositionLimiter()
        self.calibration: Calibration = calibration or RollerCalibration.from_data(
            subentry.data.get(CONF_CALIBRATION)
        )
        self.adapter = CoverAdapter(hass, self.config.cover)
        self.tracker = DirectionTracker()
        self.tracker.observe(self.adapter.module_position())
        self.decision = Decision(None, Reason.IDLE)
        self.paused = False  # e.g. while the calibration assistant moves the shutter

    # --- settings that are entities --------------------------------------------------------------
    @property
    def automatic(self) -> bool:
        return bool(self.store.get(self.id, KEY_AUTOMATIC, True))

    def set_automatic(self, on: bool) -> None:
        self.store.set(self.id, KEY_AUTOMATIC, on)

    @property
    def max_position(self) -> int:
        return int(self.store.get(self.id, KEY_MAX_POSITION, self.default_max))

    def set_max_position(self, value: int) -> None:
        self.store.set(self.id, KEY_MAX_POSITION, int(value))

    # --- position ---------------------------------------------------------------------------------
    def observe(self) -> None:
        """The physical cover reported a new position."""
        self.tracker.observe(self.adapter.module_position())

    def direction(self) -> Direction:
        return self.tracker.current(self.adapter.module_position())

    def position(self) -> int | None:
        """Real position of the shutter (calibrated)."""
        module = self.adapter.module_position()
        if module is None:
            return None
        return self.calibration.from_module(module, self.direction())

    def _module_target(self, position: int) -> tuple[int, Direction]:
        current = self.position()
        direction = Direction.UP if current is None or position >= current else Direction.DOWN
        return self.calibration.to_module(position, direction), direction

    async def _move(self, position: int, automatic: bool) -> None:
        module, direction = self._module_target(position)
        if module != self.adapter.module_position():
            self.tracker.expect(direction)
        await self.adapter.async_move(module, automatic=automatic)

    # --- control ----------------------------------------------------------------------------------
    async def async_evaluate(self, inputs: Inputs, storm: bool = False) -> Decision:
        if not self.automatic or self.paused:
            self.decision = Decision(None, Reason.OFF if not self.automatic else Reason.CALIBRATING)
            return self.decision
        ctx = ShutterContext(self.config, inputs, self.position(), self.max_position)
        decision = self.chain.decide(ctx)
        if decision.position is not None:
            target = self.limiter.limit(decision.position, self.max_position, storm)
            decision = Decision(target, decision.reason)
            if ctx.position is None or target != ctx.position:
                await self._move(target, automatic=True)
        self.decision = decision
        return decision

    async def async_manual(self, position: int) -> None:
        """A user moves the shutter through our cover entity: no limits, calibrated."""
        await self._move(max(0, min(100, int(position))), automatic=False)

    async def async_stop(self) -> None:
        await self.adapter.async_stop()

    def calibration_points(self) -> dict:
        return dict((self.subentry_data.get(CONF_CALIBRATION) or {}).get("points") or {})
