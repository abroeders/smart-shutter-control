"""Calibration assistant session: what to measure next, moving the shutter, collecting points (#10)."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from .controller import ShutterController
from .core.calibration import RollerCalibration
from .core.model import Direction

POLL = 0.5  # s between position checks
STABLE = 3.0  # s the position must stay at the target
MAX_WAIT = 180.0  # s before the assistant goes on anyway
LIFT_STEP = 2  # % module position per step while looking for the lift point
LIFT_MAX = 40  # % module position: stop looking beyond this
POINTS = (25, 50, 75)


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

    @classmethod
    def full(cls, controller: ShutterController, height_cm: float | None) -> CalibrationSession:
        session = cls(controller, height_cm)
        session.queue = [
            Action("goto", 0),
            *(Action("measure", m, Direction.UP) for m in POINTS),
            Action("goto", 100),
            *(Action("measure", m, Direction.DOWN) for m in reversed(POINTS)),
            Action("lift"),
        ]
        return session

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
        points = self.points[str(action.direction)]
        points[:] = [p for p in points if round(p[0] * 100) != action.module]
        points.append([action.module / 100, self.opening(value)])
        points.sort()

    def lifted(self, yes: bool) -> bool:
        """Answer at the current lift step; True when the search is over."""
        if yes or self.lift_at >= LIFT_MAX:
            self.slit["up"] = max(0, self.lift_at - LIFT_STEP) / 100
            return True
        return False

    def data(self) -> dict:
        return {"window_height_cm": self.height_cm, "points": self.points, "slit": self.slit}

    def summary(self) -> dict:
        calibration = RollerCalibration.from_data(self.data())
        return calibration.summary() if isinstance(calibration, RollerCalibration) else {}

    # --- moving ---------------------------------------------------------------------------------
    async def move(self, module: int) -> None:
        """Move with the module's own positions (no calibration, no limits) and wait until it is there."""
        adapter = self.controller.adapter
        if adapter.module_position() != module:
            current = adapter.module_position() or 0
            self.controller.tracker.expect(Direction.UP if module > current else Direction.DOWN)
            await adapter.async_move(module)
        start = time.monotonic()
        stable_since: float | None = None
        while time.monotonic() - start < MAX_WAIT:
            now = time.monotonic()
            if adapter.module_position() is not None and abs(adapter.module_position() - module) <= 1:
                stable_since = stable_since or now
                if now - stable_since >= STABLE:
                    self.reached = True
                    return
            else:
                stable_since = None
            await asyncio.sleep(POLL)
        self.reached = False
