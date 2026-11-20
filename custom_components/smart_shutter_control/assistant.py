"""Calibration assistant session: what to measure next, moving the shutter, collecting points (#10)."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from .controller import ShutterController
from .core.calibration import RollerCalibration
from .core.model import Direction

POLL = 0.5  # s between position checks
STABLE = 3.0  # s without a position change: the shutter has stopped
MIN_RUN = 2.0  # s after a command before a stop counts (the module may report late)
END_SETTLE = 5.0  # s extra after an end position: the module runs on to its limit switch
RETRIES = 2  # times a command is sent again when the shutter stopped short of its target
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

    @classmethod
    def full(cls, controller: ShutterController, height_cm: float | None) -> CalibrationSession:
        """First find where the bottom bar leaves the sill, then measure above it in both directions."""
        session = cls(controller, height_cm)
        session.queue = [Action("goto", 0), Action("lift")]
        return session

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

    def summary(self) -> dict:
        calibration = RollerCalibration.from_data(self.data())
        return calibration.summary() if isinstance(calibration, RollerCalibration) else {}

    # --- moving ---------------------------------------------------------------------------------
    async def move(self, module: int) -> None:
        """Move with the module's own positions (no calibration, no limits) and wait until it stops.

        A module that gets a command while it is still running on to a limit switch may stop short of the
        target; then the command is sent again.
        """
        adapter = self.controller.adapter
        self.reached = False
        for _attempt in range(1 + RETRIES):
            current = adapter.module_position()
            if current is not None and abs(current - module) <= 1:
                self.reached = True
                break
            self.controller.tracker.expect(Direction.UP if module > (current or 0) else Direction.DOWN)
            await adapter.async_move(module)
            await self._wait_until_stopped()
        if self.reached and module in (0, 100):
            await asyncio.sleep(END_SETTLE)

    async def _wait_until_stopped(self) -> None:
        adapter = self.controller.adapter
        start = last_change = time.monotonic()
        last = adapter.module_position()
        while time.monotonic() - start < MAX_WAIT:
            await asyncio.sleep(POLL)
            now = time.monotonic()
            position = adapter.module_position()
            if position != last:
                last, last_change = position, now
            elif now - start >= MIN_RUN and now - last_change >= STABLE:
                return
