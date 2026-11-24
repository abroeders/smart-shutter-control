"""One shutter: decides with the rule chain, limits, calibrates and moves through the adapter."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from homeassistant.config_entries import ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util

from . import units
from .adapter import CoverAdapter
from .const import CONF_HORIZON, DOMAIN
from .core.arrival import ArrivalCheck, State, Verdict
from .core.calibration import Calibration, PositionMemory, RollerCalibration
from .core.contacts import Floor, OpeningGuard, Target, raise_to
from .core.daily import SleepIn
from .core.heat import SunSettings
from .core.horizon import Horizon
from .core.limits import PositionLimiter
from .core.manual import ManualDetector, ManualPause, matches
from .core.model import Decision, Direction, Inputs, Reason, ShutterContext
from .core.rule_factory import build_rules
from .core.rules import RuleChain
from .core.schedule import DaySchedule, HolidayCalendar, Phase, SunTimes, merged, overridden
from .core.sun import SunPosition, WindowGeometry
from .core.sunny import ClearSkyReference, LuxBaseline, SunnyDetector
from .shutter_settings import ShutterSettings
from .storage import RuntimeStore, StoredSetting

_LOGGER = logging.getLogger(__name__)

KEY_AUTOMATIC = "automatic"
KEY_CLEAR_SKY_LUX = "clear_sky_lux"
KEY_MAX_POSITION = "max_position"
KEY_HEAT_PROTECTION = "heat_protection"
KEY_SHADING_POSITION = "shading_position"
KEY_GLARE_PROTECTION = "glare_protection"
KEY_GLARE_POSITION = "glare_position"
KEY_GLARE_FROM = "glare_from"
KEY_SLEEP_IN = "sleep_in"
KEY_PAUSE = "pause"
KEY_POSITION = "position"  # the last command and direction (#75)
RUNNING = 5.0  # W: the motor runs above this


class ShutterController:
    # settings that are entities: stored per shutter, the subentry's value until a user changes it
    automatic = StoredSetting(KEY_AUTOMATIC, bool, lambda c: True)
    max_position = StoredSetting(KEY_MAX_POSITION, int, lambda c: c.settings.max_position)
    heat_protection = StoredSetting(KEY_HEAT_PROTECTION, bool, lambda c: c.settings.heat_protection)
    shading_position = StoredSetting(KEY_SHADING_POSITION, int, lambda c: c.settings.shading_position)
    glare_protection = StoredSetting(KEY_GLARE_PROTECTION, bool, lambda c: c.settings.glare_protection)
    glare_position = StoredSetting(KEY_GLARE_POSITION, int, lambda c: c.settings.glare_position)
    glare_from = StoredSetting(KEY_GLARE_FROM, int, lambda c: c.settings.glare_from)  # % of the clear sky

    def __init__(
        self,
        hass: HomeAssistant,
        subentry: ConfigSubentry,
        store: RuntimeStore,
        calibration: Calibration | None = None,
        sun: SunSettings | None = None,
        base_schedule: dict | None = None,
        calendar: HolidayCalendar | None = None,
        safety: dict | None = None,
    ) -> None:
        self.hass = hass
        self.id = subentry.subentry_id
        self.title = subentry.title
        self.subentry_data = dict(subentry.data)  # written back when a horizon point is recorded (#54)
        self.settings = settings = ShutterSettings.from_data(subentry.data)
        self.config = settings.config
        self.store = store
        self.limiter = PositionLimiter()
        self.calibration: Calibration = calibration or RollerCalibration.from_data(settings.calibration)
        self.adapter = CoverAdapter(hass, self.config.cover, settings.motor_power)
        self.adapter.on_send = self._on_send
        self.memory = PositionMemory.from_dict(store.get(self.id, KEY_POSITION))
        self.memory.observe(self.adapter.module_position())
        self.memory.on_change = self._save_position
        self.decision = Decision(None, Reason.IDLE)
        self.paused = False  # while the calibration assistant moves the shutter
        self.paused_all = False  # automatic control of the whole integration is off (#53)

        # schedule (#4): the base schedule with this shutter's overrides
        self.schedule_values = merged(base_schedule, settings.schedule_overrides)
        self.schedule = DaySchedule(
            self.schedule_values,
            SunTimes(hass.config.latitude, hass.config.longitude),
            calendar or HolidayCalendar(),
            dt_util.get_default_time_zone(),  # not ZoneInfo(...): that can read from disk (#87)
        )
        stored_sleep = store.get(self.id, KEY_SLEEP_IN) or {}
        self.sleep_in = SleepIn(bool(stored_sleep.get("armed")), float(stored_sleep.get("armed_at", 0.0)))
        self.sleep_in.on_change = self._save_sleep_in
        # manual operation (#5)
        self.detector = ManualDetector(settings.travel_time)
        self.arrival = ArrivalCheck(settings.travel_time)  # (#48)
        self._checking = False
        self.detector.observe(self.adapter.module_position(), self._motor_running(), time.time())
        self.pause = ManualPause.from_dict(store.get(self.id, KEY_PAUSE))
        safety = safety or {}
        self.rules = build_rules(
            self.schedule,
            self.schedule_values,
            settings.sun(sun or SunSettings()),
            self.sleep_in,
            self.pause,
            self.slit_module,
            self._wanted_without_storm,
            safety.get("close_above"),
            safety.get("close_below"),
        )
        self.chain: RuleChain = self.rules.chain
        # window and door contacts (#49)
        self.contacts = (settings.opened_contact, settings.tilted_contact)
        self.guard = OpeningGuard(settings.lockout_position, settings.ventilation_position)
        self.floor_entry: dict | None = None  # the contacts' line in the decision trace
        self.on_manual: Callable[[], None] | None = None
        self.storm = False  # the last evaluation was in a storm
        self.last_target: tuple[str, int] | None = None  # what was last sent: ("real" | "module", value)

    def set_automatic(self, on: bool) -> None:
        self.automatic = on
        if on:
            self.resume()

    def set_sleep_in(self, on: bool) -> None:
        self.sleep_in.arm(on, time.time())

    def _save_sleep_in(self) -> None:
        self.store.set(
            self.id, KEY_SLEEP_IN, {"armed": self.sleep_in.armed, "armed_at": self.sleep_in.armed_at}
        )

    def _save_position(self) -> None:
        self.store.set(self.id, KEY_POSITION, self.memory.to_dict())

    def _save_pause(self) -> None:
        self.store.set(self.id, KEY_PAUSE, self.pause.to_dict())

    # --- facade light sensor (sun source: light sensors) ---------------------------------------------
    facade_light: str | None = None
    facade: SunnyDetector | None = None

    def use_facade(self, threshold: float, baseline: LuxBaseline) -> None:
        """Let this shutter's own light sensor decide whether it is sunny (only with the light source)."""
        self.facade_light = self.settings.facade_light
        if self.facade_light:
            stored = self.store.get(self.id, KEY_CLEAR_SKY_LUX)
            self.facade = SunnyDetector(ClearSkyReference.from_dict(stored), threshold, baseline=baseline)

    def facade_lux(self) -> float | None:
        state = self.hass.states.get(self.facade_light) if self.facade_light else None
        try:
            return float(state.state) if state else None
        except ValueError:
            return None

    def _with_facade(self, inputs: Inputs, weather: str | None = None) -> Inputs:
        if self.facade is None or inputs.sun is None:
            return inputs
        lux = self.facade_lux()
        sunny = self.facade.update(inputs.sun, lux, weather, inputs.now)
        if lux is not None:
            self.store.set(self.id, KEY_CLEAR_SKY_LUX, self.facade.reference.to_dict())
        return replace(inputs, sunny=sunny, sun_factor=self.facade.factor)

    def room_temperature(self) -> float | None:
        """In °C, whatever the sensor's unit (#64)."""
        entity_id = self.config.room_temperature
        return units.temperature(self.hass.states.get(entity_id) if entity_id else None)

    def slit_module(self) -> int:
        """Module position of the slit: from the calibration, else the schedule's setting."""
        slit = self.calibration.slit(Direction.UP)
        return int(slit if slit is not None else self.schedule_values["slit_module"])

    def overrides(self) -> list[str]:
        return overridden(self.settings.schedule_overrides)

    # --- position ---------------------------------------------------------------------------------
    def _motor_running(self) -> bool | None:
        power = self.adapter.motor_power()
        return None if power is None else power > RUNNING

    def observe(self) -> None:
        """The physical cover or its power sensor reported."""
        module = self.adapter.module_position()
        self.memory.observe(module)
        now = time.time()
        if self.detector.observe(module, self._motor_running(), now):
            self._manual(now, "switch")

    def _on_send(self, module: int, before: int | None, automatic: bool) -> None:
        self.detector.sent(module, before, time.time())
        if not self.paused:  # the calibration assistant checks its own moves
            self.arrival.sent(module, time.time())
        if not automatic:
            self._manual(time.time(), "entity")

    def _wanted_without_storm(self, ctx: ShutterContext) -> int | None:
        """The real position the other rules want now (the slit counts as closed), for the storm's end."""
        decision = self.chain.decide(ctx, skip=self.rules.storm)
        if decision.module is not None:
            return 0
        return decision.position

    def _manual(self, now: float, source: str) -> None:
        """Someone moved the shutter: end sleep-in, pause automatic control (unless the mode is ignore)."""
        if self.sleep_in.armed:
            self.sleep_in.arm(False, now)
        if source == "switch":  # moved by someone else: whatever we sent is no longer the goal
            self.arrival.cancel()
            self.memory.forget_sent()
        mode = str(self.schedule_values["manual_mode"])
        duration = float(self.schedule_values["manual_duration"])
        self.pause.start(now, mode, duration, str(self.rules.schedule.phase(now)), source)
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
        return self.memory.current(self.adapter.module_position())

    def position(self) -> int | None:
        """Real position of the shutter (calibrated)."""
        return self.memory.real(self.adapter.module_position(), self.calibration)

    def phase(self, now: float | None = None) -> Phase:
        return self.rules.schedule.phase(time.time() if now is None else now)

    def next_change(self):
        return self.schedule.next_change(datetime.now(UTC))

    def next_changes(self, count: int) -> list:
        """The next `count` phase changes of the schedule."""
        changes, at = [], datetime.now(UTC)
        while len(changes) < count and (change := self.schedule.next_change(at)) is not None:
            changes.append(change)
            at = change.at
        return changes

    def target_of(self, phase: Phase) -> int | str:
        return "slit" if phase is Phase.SLIT else self.schedule.target(phase)

    def moving(self) -> str | None:
        """opening or closing while the physical cover moves (its state, else the motor power)."""
        state = self.hass.states.get(self.config.cover)
        if state is not None and state.state in ("opening", "closing"):
            return state.state
        if self._motor_running():
            return "opening" if self.direction() is Direction.UP else "closing"
        return None

    def _module_target(self, position: int) -> tuple[int, Direction]:
        current = self.position()
        direction = Direction.UP if current is None or position >= current else Direction.DOWN
        return self.calibration.to_module(position, direction), direction

    async def _move(self, position: int, automatic: bool) -> None:
        module, direction = self._module_target(position)
        self.memory.command(module, position, direction, self.adapter.module_position())
        await self.adapter.async_move(module, automatic=automatic)

    async def _move_module(self, module: int) -> None:
        current = self.adapter.module_position()
        if current is not None and module != current:
            self.memory.command(module, None, Direction.UP if module > current else Direction.DOWN, current)
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
            glare_protection=self.glare_protection,
            glare_position=self.glare_position,
            glare_from=self.glare_from / 100,
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

    def window(self) -> WindowGeometry:
        c = self.config
        return WindowGeometry(c.azimuth, c.tilt, c.min_elevation, c.max_elevation, c.horizon)

    def horizon_with(self, sun: SunPosition) -> Horizon:
        """The horizon with a point where the sun leaves the window now (just above it: off at once)."""
        return self.config.horizon.with_point(sun.azimuth, sun.elevation + 0.1)

    def set_horizon(self, horizon: Horizon) -> None:
        self.config = replace(self.config, horizon=horizon)
        self.subentry_data[CONF_HORIZON] = horizon.as_data()

    # --- arrival (#48) ---------------------------------------------------------------------------------
    @property
    def stuck(self) -> bool:
        return self.arrival.state is State.STUCK

    async def async_check_arrival(self) -> None:
        """When a command is due: ask the module where it is; send once more, or report the shutter stuck."""
        now = time.time()
        if self._checking or not self.arrival.due(self._motor_running(), now):
            return
        self._checking = True
        try:
            await self.adapter.async_refresh()  # not every module reports by itself (#42)
            position = self.adapter.module_position()
            verdict = self.arrival.judge(position)
            if verdict is Verdict.ARRIVED:
                ir.async_delete_issue(self.hass, DOMAIN, self.issue_id)
            elif verdict is Verdict.RETRY:
                command = self.adapter.last_command
                _LOGGER.info(
                    "%s did not reach %s %% (at %s %%): sending it again",
                    self.title,
                    self.arrival.target,
                    position,
                )
                await self.adapter.async_move(
                    self.arrival.target, automatic=command.automatic if command else True
                )
            else:
                _LOGGER.warning(
                    "%s did not reach %s %% (at %s %%)", self.title, self.arrival.target, position
                )
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    self.issue_id,
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="stuck",
                    translation_placeholders={
                        "name": self.title,
                        "target": str(self.arrival.target),
                        "position": "?" if position is None else str(position),
                    },
                )
        finally:
            self._checking = False

    @property
    def issue_id(self) -> str:
        return f"stuck_{self.id}"

    def trace(self) -> list[dict]:
        """What every rule said in the last decision (#56); empty while automatic control is off."""
        if not self.automatic or self.paused or self.paused_all:
            return []
        entries = [entry.as_dict() for entry in self.chain.last_trace]
        return [self.floor_entry, *entries] if self.floor_entry else entries

    async def async_evaluate(
        self, inputs: Inputs, storm: bool = False, weather: str | None = None, paused: bool = False
    ) -> Decision:
        """`paused`: automatic control of the whole integration is off (#53), storm included."""
        self.observe()  # a report not handled yet must not count as manual after this decision
        if self._read_contacts(inputs.now) and self.pause.on:
            self.resume()  # a door that opens ends a manual pause: the shutter goes up (#49)
        self.storm = inputs.storm
        self.paused_all = paused
        if self.paused or paused:
            self.arrival.cancel()
        if not self.automatic or self.paused or paused:
            reason = Reason.CALIBRATING if self.paused else Reason.PAUSED if paused else Reason.OFF
            self.decision = Decision(None, reason)
            return self.decision
        inputs = self._with_facade(inputs, weather)
        ctx = self._context(inputs)
        if self.pause.on and self.detector.at_rest(inputs.now):
            # moved by hand to where automatic control wants it: resume (#5)
            wanted = self._limited(self.chain.decide(ctx, skip=self.rules.pause), storm)
            if wanted is not None and self._there(wanted):
                self.resume()
                self.last_target = wanted
        storm = storm or inputs.storm
        decision = self.chain.decide(ctx)
        target = self._limited(decision, storm)
        decision, target = self._with_floor(decision, target, storm, inputs.now)
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

    # --- contacts (#49) -------------------------------------------------------------------------------
    def _read_contacts(self, now: float) -> bool:
        """Read both contacts; true when the door or window has just opened."""
        return self.guard.update(*(self._contact(e) for e in self.contacts), now)

    def _contact(self, entity_id: str | None) -> bool | None:
        if not entity_id:
            return False
        state = self.hass.states.get(entity_id)
        if state is None or state.state not in ("on", "off"):
            return None  # unavailable: keep the last state
        return state.state == "on"

    def _current(self) -> Target | None:
        position = self.position()
        if position is None:
            return None
        slit = ("module", self.slit_module())
        return slit if position == 0 and self._there(slit) else ("real", position)

    def _with_floor(
        self, decision: Decision, target: Target | None, storm: bool, now: float
    ) -> tuple[Decision, Target | None]:
        """Keep the shutter at least at the lockout or ventilation position; frost and a manual pause
        leave it where it is."""
        floor = self.guard.floor(now, self.slit_module(), self.max_position)
        leave = decision.final and decision.position is None
        raised = target if leave else raise_to(target, self._current(), floor, storm)
        applied = floor is not None and raised != target
        self.floor_entry = _floor_entry(floor, applied, self.guard) if any(self.contacts) else None
        if not applied:
            return decision, target
        kind, value = raised
        module = value if kind == "module" else None
        return Decision(0 if module is not None else value, floor.reason, module=module), raised

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
        return self.settings.calibration_points

    def next_action(self) -> dict[str, Any]:
        """The next schedule change as the next action sensor shows it; empty without one."""
        change = self.next_change()
        if change is None:
            return {}
        return {
            "at": change.at.isoformat(),
            "phase": change.phase.value,
            "position": self.target_of(change.phase),
            "following": [
                {"at": t.at.isoformat(), "phase": t.phase.value, "position": self.target_of(t.phase)}
                for t in self.next_changes(3)[1:]
            ],
            "overrides": self.overrides(),
        }

    def diagnostics(self) -> dict[str, Any]:
        """The shutter's runtime state for the diagnostics file: what its entities show."""
        return {
            "title": self.title,
            "subentry_id": self.id,
            "cover": self.config.cover,
            "data": dict(self.subentry_data),
            "state": {
                "position": self.position(),
                "module_position": self.adapter.module_position(),
                "phase": self.phase().value,
                "reason": str(self.decision.reason),
                "target_position": self.decision.position,
                "manual_pause": self.pause.on,
                "stuck": self.stuck,
                "calibrated": self.calibration.calibrated,
            },
            "decision": self.trace(),
            "next_action": self.next_action(),
            "position_memory": self.memory.to_dict(),
        }

    def pause_info(self) -> dict[str, Any]:
        p = self.pause
        return {
            "since": _iso(p.since),
            "until": "next phase" if p.until_next_phase else _iso(p.until),
            "source": p.source or None,
        }


def _floor_entry(floor: Floor | None, applied: bool, guard: OpeningGuard) -> dict:
    """The contacts' line in the decision trace (#56); a position None is the slit."""
    if floor is None:
        return {"rule": "contacts", "priority": 0, "result": "none", "why": "contacts_closed"}
    kind, value = floor.target
    position = None if kind == "module" else value
    why = "opened" if floor.reason == Reason.LOCKOUT else "tilted"
    if not (guard.opened.on if why == "opened" else guard.tilted.on):
        why += "_hold"
    return {
        "rule": "contacts",
        "priority": 0,
        "result": "floor",
        "position": position,
        "applied": applied,
        "why": why,
    }


def _iso(epoch: float | None) -> str | None:
    return None if epoch is None else datetime.fromtimestamp(epoch, UTC).isoformat()
