"""Calibration assistant session: what to measure next, moving the shutter, collecting points (#10)."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from homeassistant.util import dt as dt_util

from .controller import ShutterController
from .core.calibration import RollerCalibration
from .core.model import Direction

POLL = 0.5  # s between checks
REFRESH = 5.0  # s between asking the module for its position while waiting: not every module reports
RUNNING_W = 5.0  # motor power above this: the motor runs
START_WAIT = 6.0  # s for the motor to start after a command
IDLE = 2.0  # s of motor power below RUNNING_W: the motor has stopped
REPORT_WAIT = 30.0  # s after the motor stopped for a fresh position report (modules report up to ~20 s late)
STABLE = 12.0  # without a power sensor and travel time: s without a position change
END_SETTLE = 5.0  # s extra after an end position: the module runs on to its limit switch
END_STABLE_NO_POWER = 15.0  # s the end position must be reported unchanged without a power sensor (#18)
END_SETTLE_NO_POWER = 15.0  # s run-on after an end position without a power sensor (#18)
TRAVEL_MARGIN = 5.0  # s added to the expected travel without a power sensor (#18)
RETRIES = 2  # times a command is sent again when the shutter stopped short of an intermediate target
MAX_WAIT = 180.0  # s per attempt before the assistant goes on anyway
LIFT_STEP = 2  # % module position per step while looking for the lift point
LIFT_MAX = 40  # % module position: stop looking beyond this
SPREAD = (0.15, 0.40, 0.65, 0.90)  # measuring points as shares of the travel above the lift point


@dataclass
class Action:
    kind: str  # goto, measure, lift
    module: int = 0
    direction: Direction = Direction.UP


@dataclass
class CalibrationSession:
    controller: ShutterController
    height_cm: float | None = None
    points: dict[str, list[list[float]]] = field(default_factory=lambda: {"up": [], "down": []})
    slit: dict[str, float] = field(default_factory=dict)
    queue: list[Action] = field(default_factory=list)
    lift_at: int = 0
    reached: bool = True  # the last move ended at its target
    measuring: list[int] = field(default_factory=list)  # module positions of the measuring points
    travel_time: float | None = None  # s, fully open to fully closed (#18)
    _refreshed: float = 0.0  # monotonic time of the last refresh request
    measured_travel: bool = False

    @property
    def has_power(self) -> bool:
        return self.controller.adapter.motor_power() is not None

    @classmethod
    def full(
        cls, controller: ShutterController, height_cm: float | None, travel_time: float | None = None
    ) -> CalibrationSession:
        """First find where the bottom bar leaves the sill, then measure above it in both directions.

        Without a motor power sensor and without a known travel time, the travel time is measured first.
        """
        session = cls(controller, height_cm, travel_time=travel_time)
        timing = [Action("time")] if not session.has_power and not travel_time else [Action("goto", 0)]
        session.queue = [*timing, Action("lift")]
        return session

    async def measure_travel(self) -> None:
        """Fully open, then time the travel to fully closed (until the module reports 0)."""
        await self.move(100)
        start = time.monotonic()
        self.controller.memory.expect(Direction.DOWN, self.controller.adapter.module_position())
        await self.controller.adapter.async_move(0)
        first = await self._wait_for_end(0)
        if first is not None:
            self.travel_time = round(first - start, 1)
            self.measured_travel = True
            self.reached = True
            await asyncio.sleep(END_SETTLE_NO_POWER)

    def plan_measuring(self, lift: int) -> None:
        """Points spread over the travel above the lift point: none of them on the sill."""
        span = 100 - lift
        self.measuring = sorted({min(99, max(lift + 2, round(lift + span * f))) for f in SPREAD})
        self.queue += [
            *(Action("measure", m, Direction.UP) for m in self.measuring),
            Action("goto", 100),
            *(Action("measure", m, Direction.DOWN) for m in reversed(self.measuring)),
        ]

    @classmethod
    def one_point(
        cls, controller: ShutterController, stored: dict, module: int, direction: Direction
    ) -> CalibrationSession:
        session = cls(controller, stored.get("window_height_cm"))
        session.points = {
            k: [list(p) for p in v] for k, v in (stored.get("points") or {"up": [], "down": []}).items()
        }
        session.points.setdefault("up", [])
        session.points.setdefault("down", [])
        session.slit = dict(stored.get("slit") or {})
        session.queue = [
            Action("goto", 0 if direction is Direction.UP else 100),
            Action("measure", module, direction),
        ]
        return session

    # --- measurements ---------------------------------------------------------------------------
    def opening(self, value: float) -> float:
        """A measured opening (cm with a window height, else %) as a fraction of the window."""
        if self.height_cm:
            return max(0.0, min(1.0, value / self.height_cm))
        return max(0.0, min(1.0, value / 100))

    def add_point(self, action: Action, value: float) -> None:
        opening = self.opening(value)
        points = self.points[str(action.direction)]
        points[:] = [p for p in points if round(p[0] * 100) != action.module]
        points.append([action.module / 100, opening])
        points.sort()
        if opening == 0 and self.measuring:
            self._still_on_sill(action)

    def _still_on_sill(self, action: Action) -> None:
        """The bottom bar is still on the sill at a measuring point: measure higher instead."""
        if action.direction is Direction.UP:
            higher = [m for m in self.measuring if m > action.module]
            extra = (action.module + higher[0]) // 2 if higher else min(99, action.module + 5)
            if extra not in self.measuring and extra > action.module:
                self.measuring.append(extra)
                self.measuring.sort()
                self.queue.insert(0, Action("measure", extra, Direction.UP))
        else:  # going down, the lower points are on the sill too
            self.queue = [
                a
                for a in self.queue
                if not (a.kind == "measure" and a.direction is Direction.DOWN and a.module < action.module)
            ]

    def lifted(self, yes: bool) -> bool:
        """Answer at the current lift step; True when the search is over."""
        if yes or self.lift_at >= LIFT_MAX:
            self.slit["up"] = max(0, self.lift_at - LIFT_STEP) / 100
            if not self.measuring and not self.queue:
                self.plan_measuring(self.lift_at)
            return True
        return False

    def data(self) -> dict:
        return {"window_height_cm": self.height_cm, "points": self.points, "slit": self.slit}

    def updates(self) -> dict:
        """What the assistant saves in the shutter's settings."""
        from .const import CONF_CALIBRATION, CONF_TRAVEL_TIME

        out = {CONF_CALIBRATION: self.data()}
        if self.measured_travel and self.travel_time:
            out[CONF_TRAVEL_TIME] = self.travel_time
        return out

    def summary(self) -> dict:
        calibration = RollerCalibration.from_data(self.data())
        return calibration.summary() if isinstance(calibration, RollerCalibration) else {}

    # --- moving ---------------------------------------------------------------------------------
    async def move(self, module: int) -> None:
        """Move with the module's own positions (no calibration, no limits) and wait until it is there.

        End positions (0, 100) get one uninterrupted command and are confirmed by the module reporting the
        end with the motor stopped: the module runs to its limit switch. Intermediate positions are sent
        again when the motor stopped short of them (a command during the run-on of a limit switch can stop
        early).
        """
        adapter = self.controller.adapter
        self.reached = False
        end = module in (0, 100)
        for _attempt in range(1 if end else 1 + RETRIES):
            current = adapter.module_position()
            there = current == module or (not end and current is not None and abs(current - module) <= 1)
            if there and not self._motor_running():
                self.reached = True
                break
            self.controller.memory.expect(
                Direction.UP if module > (current or 0) else Direction.DOWN, current
            )
            await adapter.async_move(module)
            if end:
                self.reached = await self._wait_for_end(module) is not None
            else:
                await self._wait_until_stopped(current, module)
                position = adapter.module_position()
                self.reached = position is not None and abs(position - module) <= 1
            if self.reached:
                break
        if self.reached and end:
            await asyncio.sleep(END_SETTLE if self.has_power else END_SETTLE_NO_POWER)

    async def _pause(self) -> None:
        """Wait one check interval; every REFRESH seconds also ask the module for its position (without
        waiting for the answer), so a module that does not report by itself is still seen to arrive."""
        await asyncio.sleep(POLL)
        now = time.monotonic()
        if now - self._refreshed >= REFRESH:
            self._refreshed = now
            self.controller.hass.async_create_task(self.controller.adapter.async_refresh())

    def _at(self, target: int | None) -> bool:
        """The module reports the target (±1) and the motor does not run."""
        position = self.controller.adapter.module_position()
        return (
            target is not None
            and position is not None
            and abs(position - target) <= 1
            and not self._motor_running()
        )

    def _motor_running(self) -> bool:
        power = self.controller.adapter.motor_power()
        return power is not None and power > RUNNING_W

    async def _fresh_report(self) -> None:
        """Ask the module for its position and wait for a report that came after the motor stopped."""
        adapter = self.controller.adapter
        stopped = dt_util.utcnow()
        await adapter.async_refresh()
        start = time.monotonic()
        self._refreshed = time.monotonic()
        while time.monotonic() - start < REPORT_WAIT:
            if adapter.reported_since(stopped):
                return
            await self._pause()

    async def _wait_for_end(self, module: int) -> float | None:
        """Until the module reports the end position and the motor has been idle for a while (without a
        power sensor: the end reported unchanged for a while). Returns when the end was first reported."""
        adapter = self.controller.adapter
        hold = IDLE if self.has_power else END_STABLE_NO_POWER
        start = time.monotonic()
        idle_since: float | None = None
        while time.monotonic() - start < MAX_WAIT:
            await self._pause()
            now = time.monotonic()
            if adapter.module_position() == module and not self._motor_running():
                idle_since = idle_since or now
                if now - idle_since >= hold:
                    return idle_since
            else:
                idle_since = None
        return None

    async def _wait_until_stopped(self, start_position: int | None = None, target: int | None = None) -> None:
        """Until the motor stops (with a power sensor); without one for the expected travel time (#18), or
        until the position stops changing when the travel time is unknown."""
        adapter = self.controller.adapter
        start = time.monotonic()
        if (
            adapter.motor_power() is None
            and self.travel_time
            and start_position is not None
            and target is not None
        ):
            expected = abs(target - start_position) / 100 * self.travel_time + TRAVEL_MARGIN
            while time.monotonic() - start < expected:
                await self._pause()
            await self._fresh_report()
            return
        if adapter.motor_power() is not None:
            started = False
            idle_since: float | None = None
            while time.monotonic() - start < MAX_WAIT:
                await self._pause()
                now = time.monotonic()
                if self._motor_running():
                    started, idle_since = True, None
                    continue
                if not started and now - start < START_WAIT and not self._at(target):
                    continue  # not started yet (a short move may be over before the power sensor shows it)
                idle_since = idle_since or now
                if now - idle_since >= IDLE:
                    await self._fresh_report()
                    return
            return
        last_change = start
        last = adapter.module_position()
        while time.monotonic() - start < MAX_WAIT:
            await self._pause()
            now = time.monotonic()
            position = adapter.module_position()
            if position != last:
                last, last_change = position, now
                if self._at(target):
                    return  # arrived: no need to wait until the position has been stable for a while
            elif now - last_change >= STABLE:
                return
