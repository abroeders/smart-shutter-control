"""One shutter: decides with the rule chain, limits, calibrates and moves through the adapter."""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from homeassistant.config_entries import ConfigSubentry
from homeassistant.core import HomeAssistant

from .adapter import CoverAdapter
from .const import (
    CONF_AZIMUTH,
    CONF_CALIBRATION,
    CONF_COVER,
    CONF_HEAT_OUTDOOR,
    CONF_HEAT_PROTECTION,
    CONF_HEAT_ROOM,
    CONF_MAX_ELEVATION,
    CONF_MAX_POSITION,
    CONF_MIN_ELEVATION,
    CONF_MOTOR_POWER,
    CONF_ROOM_TEMPERATURE,
    CONF_SCHEDULE,
    CONF_SHADING_POSITION,
    CONF_TILT,
    CONF_TRAVEL_TIME,
    DEFAULT_SHUTTER,
)
from .core.calibration import Calibration, DirectionTracker, RollerCalibration
from .core.daily import ScheduleRule, SleepIn, SleepInRule
from .core.heat import HeatProtectionRule, SunSettings
from .core.limits import PositionLimiter
from .core.manual import ManualDetector, ManualPause, ManualPauseRule, matches
from .core.model import Decision, Direction, Inputs, Reason, ShutterConfig, ShutterContext
from .core.rules import RuleChain
from .core.schedule import DaySchedule, HolidayCalendar, Phase, SunTimes, merged, overridden
from .core.weather import FrostRule, StormRule, TemperatureLimitRule
from .storage import RuntimeStore

KEY_AUTOMATIC = "automatic"
KEY_MAX_POSITION = "max_position"
KEY_HEAT_PROTECTION = "heat_protection"
KEY_SHADING_POSITION = "shading_position"
KEY_SLEEP_IN = "sleep_in"
KEY_PAUSE = "pause"
RUNNING = 5.0  # W: the motor runs above this


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
        sun: SunSettings | None = None,
        base_schedule: dict | None = None,
        calendar: HolidayCalendar | None = None,
        safety: dict | None = None,
    ) -> None:
        self.hass = hass
        self.id = subentry.subentry_id
        self.title = subentry.title
        self.subentry_data = dict(subentry.data)
        self.config = shutter_config(dict(subentry.data))
        self.default_max = int(subentry.data.get(CONF_MAX_POSITION, DEFAULT_SHUTTER[CONF_MAX_POSITION]))
        self.store = store
        sun = sun or SunSettings()
        overrides = {
            "heat_outdoor": subentry.data.get(CONF_HEAT_OUTDOOR),
            "heat_room": subentry.data.get(CONF_HEAT_ROOM),
        }
        sun = SunSettings(**{**sun.__dict__, **{k: float(v) for k, v in overrides.items() if v is not None}})
        self.default_heat = bool(
            subentry.data.get(CONF_HEAT_PROTECTION, DEFAULT_SHUTTER[CONF_HEAT_PROTECTION])
        )
        self.default_shading = int(
            subentry.data.get(CONF_SHADING_POSITION, DEFAULT_SHUTTER[CONF_SHADING_POSITION])
        )
        self.limiter = PositionLimiter()
        self.calibration: Calibration = calibration or RollerCalibration.from_data(
            subentry.data.get(CONF_CALIBRATION)
        )
        self.adapter = CoverAdapter(hass, self.config.cover, subentry.data.get(CONF_MOTOR_POWER))
        self.adapter.on_send = self._on_send
        self.tracker = DirectionTracker()
        self.tracker.observe(self.adapter.module_position())
        self.decision = Decision(None, Reason.IDLE)
        self.paused = False  # while the calibration assistant moves the shutter

        # schedule (#4): the base schedule with this shutter's overrides
        self.schedule_overrides = dict(subentry.data.get(CONF_SCHEDULE) or {})
        self.schedule_values = merged(base_schedule, self.schedule_overrides)
        self.schedule = DaySchedule(
            self.schedule_values,
            SunTimes(hass.config.latitude, hass.config.longitude),
            calendar or HolidayCalendar(),
            _zone(hass),
        )
        self.schedule_rule = ScheduleRule(self.schedule, self.slit_module)
        stored_sleep = store.get(self.id, KEY_SLEEP_IN) or {}
        self.sleep_in = SleepIn(bool(stored_sleep.get("armed")), float(stored_sleep.get("armed_at", 0.0)))
        self.sleep_in.on_change = self._save_sleep_in
        # manual operation (#5)
        travel = subentry.data.get(CONF_TRAVEL_TIME)
        self.detector = ManualDetector(float(travel) if travel else None)
        self.detector.observe(self.adapter.module_position(), self._motor_running(), time.time())
        self.pause = ManualPause.from_dict(store.get(self.id, KEY_PAUSE))
        self.pause_rule = ManualPauseRule(self.pause, lambda now: str(self.schedule_rule.phase(now)))
        self.heat_rule = HeatProtectionRule(sun)
        safety = safety or {}
        self.storm_rule = StormRule(
            lambda: str(self.schedule_values["storm_position"]), self._wanted_without_storm
        )
        self.chain = chain or RuleChain(
            [
                self.storm_rule,
                FrostRule(),
                TemperatureLimitRule(safety.get("close_above"), safety.get("close_below")),
                self.pause_rule,
                SleepInRule(self.sleep_in, self.schedule),
                self.heat_rule,
                self.schedule_rule,
            ]
        )
        self.on_manual: Callable[[], None] | None = None
        self.storm = False  # the last evaluation was in a storm
        self.last_target: tuple[str, int] | None = None  # what was last sent: ("real" | "module", value)

    # --- settings that are entities --------------------------------------------------------------
    @property
    def automatic(self) -> bool:
        return bool(self.store.get(self.id, KEY_AUTOMATIC, True))

    def set_automatic(self, on: bool) -> None:
        self.store.set(self.id, KEY_AUTOMATIC, on)
        if on:
            self.resume()

    @property
    def max_position(self) -> int:
        return int(self.store.get(self.id, KEY_MAX_POSITION, self.default_max))

    def set_max_position(self, value: int) -> None:
        self.store.set(self.id, KEY_MAX_POSITION, int(value))

    @property
    def heat_protection(self) -> bool:
        return bool(self.store.get(self.id, KEY_HEAT_PROTECTION, self.default_heat))

    def set_heat_protection(self, on: bool) -> None:
        self.store.set(self.id, KEY_HEAT_PROTECTION, on)

    @property
    def shading_position(self) -> int:
        return int(self.store.get(self.id, KEY_SHADING_POSITION, self.default_shading))

    def set_shading_position(self, value: int) -> None:
        self.store.set(self.id, KEY_SHADING_POSITION, int(value))

    def set_sleep_in(self, on: bool) -> None:
        self.sleep_in.arm(on, time.time())

    def _save_sleep_in(self) -> None:
        self.store.set(
            self.id, KEY_SLEEP_IN, {"armed": self.sleep_in.armed, "armed_at": self.sleep_in.armed_at}
        )

    def _save_pause(self) -> None:
        self.store.set(self.id, KEY_PAUSE, self.pause.to_dict())

    def room_temperature(self) -> float | None:
        entity_id = self.config.room_temperature
        state = self.hass.states.get(entity_id) if entity_id else None
        try:
            return float(state.state) if state else None
        except ValueError:
            return None

    def slit_module(self) -> int:
        """Module position of the slit: from the calibration, else the schedule's setting."""
        slit = self.calibration.slit(Direction.UP)
        return int(slit if slit is not None else self.schedule_values["slit_module"])

    def overrides(self) -> list[str]:
        return overridden(self.schedule_overrides)

    # --- position ---------------------------------------------------------------------------------
    def _motor_running(self) -> bool | None:
        power = self.adapter.motor_power()
        return None if power is None else power > RUNNING

    def observe(self) -> None:
        """The physical cover or its power sensor reported."""
        module = self.adapter.module_position()
        self.tracker.observe(module)
        now = time.time()
        if self.detector.observe(module, self._motor_running(), now):
            self._manual(now, "switch")

    def _on_send(self, module: int, before: int | None, automatic: bool) -> None:
        self.detector.sent(module, before, time.time())
        if not automatic:
            self._manual(time.time(), "entity")

    def _wanted_without_storm(self, ctx: ShutterContext) -> int | None:
        """The real position the other rules want now (the slit counts as closed), for the storm's end."""
        decision = self.chain.decide(ctx, skip=self.storm_rule)
        if decision.module is not None:
            return 0
        return decision.position

    def _manual(self, now: float, source: str) -> None:
        """Someone moved the shutter: end sleep-in, pause automatic control (unless the mode is ignore)."""
        if self.sleep_in.armed:
            self.sleep_in.arm(False, now)
        mode = str(self.schedule_values["manual_mode"])
        duration = float(self.schedule_values["manual_duration"])
        self.pause.start(now, mode, duration, str(self.schedule_rule.phase(now)), source)
        self.last_target = None  # whatever ends the pause sends the wanted position again
        self._save_pause()
        if self.on_manual is not None:
            self.on_manual()

    def resume(self) -> None:
        """End a manual pause; the next evaluation moves the shutter to the wanted position."""
        self.pause.end()
        self.last_target = None
        self._save_pause()

    def direction(self) -> Direction:
        return self.tracker.current(self.adapter.module_position())

    def position(self) -> int | None:
        """Real position of the shutter (calibrated)."""
        module = self.adapter.module_position()
        if module is None:
            return None
        return self.calibration.from_module(module, self.direction())

    def phase(self, now: float | None = None) -> Phase:
        return self.schedule_rule.phase(time.time() if now is None else now)

    def next_change(self):
        return self.schedule.next_change(datetime.now(UTC))

    def _module_target(self, position: int) -> tuple[int, Direction]:
        current = self.position()
        direction = Direction.UP if current is None or position >= current else Direction.DOWN
        return self.calibration.to_module(position, direction), direction

    async def _move(self, position: int, automatic: bool) -> None:
        module, direction = self._module_target(position)
        if module != self.adapter.module_position():
            self.tracker.expect(direction)
        await self.adapter.async_move(module, automatic=automatic)

    async def _move_module(self, module: int) -> None:
        current = self.adapter.module_position()
        if current is not None and module != current:
            self.tracker.expect(Direction.UP if module > current else Direction.DOWN)
        await self.adapter.async_move(module, automatic=True)

    # --- control ----------------------------------------------------------------------------------
    def _context(self, inputs: Inputs) -> ShutterContext:
        return ShutterContext(
            self.config,
            inputs,
            self.position(),
            self.max_position,
            room=self.room_temperature(),
            heat_protection=self.heat_protection,
            shading_position=self.shading_position,
        )

    def _limited(self, decision: Decision, storm: bool) -> tuple[str, int] | None:
        if decision.module is not None:
            return ("module", decision.module)
        if decision.position is None:
            return None
        return ("real", self.limiter.limit(decision.position, self.max_position, storm))

    def _there(self, target: tuple[str, int]) -> bool:
        kind, value = target
        if kind == "module":
            module = self.adapter.module_position()
            return module is not None and abs(module - value) <= 1
        return matches(self.position(), value)

    async def async_evaluate(self, inputs: Inputs, storm: bool = False) -> Decision:
        self.observe()  # a report not handled yet must not count as manual after this decision
        self.storm = inputs.storm
        if not self.automatic or self.paused:
            self.decision = Decision(None, Reason.OFF if not self.automatic else Reason.CALIBRATING)
            return self.decision
        ctx = self._context(inputs)
        if self.pause.on and self.detector.at_rest(inputs.now):
            # moved by hand to where automatic control wants it: resume (#5)
            wanted = self._limited(self.chain.decide(ctx, skip=self.pause_rule), storm)
            if wanted is not None and self._there(wanted):
                self.resume()
                self.last_target = wanted
        storm = storm or inputs.storm
        decision = self.chain.decide(ctx)
        target = self._limited(decision, storm)
        if target is None:
            self.decision = decision
            return decision
        decision = Decision(target[1] if target[0] == "real" else 0, decision.reason, module=decision.module)
        if target != self.last_target:
            self.last_target = target
            if not self._there(target):
                if target[0] == "module":
                    await self._move_module(target[1])
                else:
                    await self._move(target[1], automatic=True)
        self.decision = decision
        return decision

    async def async_manual(self, position: int) -> None:
        """A user moves the shutter through our entities: no limits, calibrated; counts as manual.

        In a storm only the ends exist: a position in between goes to the nearest end."""
        position = max(0, min(100, int(position)))
        if self.storm and 0 < position < 100:
            position = 100 if position >= 50 and self.max_position >= 100 else 0
        await self._move(position, automatic=False)

    async def async_stop(self) -> None:
        self._manual(time.time(), "entity")
        await self.adapter.async_stop()

    def calibration_points(self) -> dict:
        return dict((self.subentry_data.get(CONF_CALIBRATION) or {}).get("points") or {})

    def pause_info(self) -> dict[str, Any]:
        p = self.pause
        return {
            "since": _iso(p.since),
            "until": "next phase" if p.until_next_phase else _iso(p.until),
            "source": p.source or None,
        }


def _iso(epoch: float | None) -> str | None:
    return None if epoch is None else datetime.fromtimestamp(epoch, UTC).isoformat()


def _zone(hass: HomeAssistant):
    from zoneinfo import ZoneInfo

    return ZoneInfo(hass.config.time_zone)
