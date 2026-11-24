"""Manual operation (#5): telling the controller's own moves from manual ones, and the pause after a
manual action. No Home Assistant imports.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import Decision, Reason, ShutterContext

MARGIN = 2  # % module position: reports within this range of the way count as the way
LATE = 30.0  # s after arrival: late reports of the target still belong to the command
NO_POWER_TRAVEL = 120.0  # s: without a power sensor a command is active at most this long (#18: measured)
MATCH = 2  # %: a manual position this close to the wanted one resumes automatic control


@dataclass
class ActiveCommand:
    target: int
    start: int | None
    sent_at: float
    arrived_at: float | None = None
    started: bool = False  # the motor ran (with a power sensor)


class ManualDetector:
    """Watches module positions and motor power; tells whether a change was caused by someone else."""

    def __init__(self, travel_time: float | None = None) -> None:
        self.command: ActiveCommand | None = None
        self.travel_time = travel_time or NO_POWER_TRAVEL
        self.last_position: int | None = None
        self.last_change = 0.0
        self.motor = False

    def sent(self, target: int, start: int | None, now: float) -> None:
        self.command = ActiveCommand(target, start, now)

    def active(self, now: float) -> bool:
        c = self.command
        if c is None:
            return False
        if (
            c.arrived_at is not None
            and now - c.arrived_at > LATE
            or c.arrived_at is None
            and now - c.sent_at > self.travel_time + LATE
        ):
            self.command = None
        return self.command is not None

    def _on_the_way(self, position: int) -> bool:
        c = self.command
        low = min(c.target, c.start if c.start is not None else c.target)
        high = max(c.target, c.start if c.start is not None else c.target)
        return low - MARGIN <= position <= high + MARGIN

    def observe(self, position: int | None, motor_running: bool | None, now: float) -> bool:
        """A new report (position and/or motor); True when it shows a manual action."""
        manual = False
        active = self.active(now)
        if motor_running is not None:
            if motor_running and not self.motor and not active:
                manual = True  # the motor started without a command
            if motor_running and active:
                self.command.started = True
            self.motor = motor_running
        if position is not None and position != self.last_position:
            if self.last_position is not None:
                if not active or not self._on_the_way(position):
                    manual = True
                self.last_change = now
            self.last_position = position
        c = self.command
        if c is not None and position is not None and abs(position - c.target) <= 1 and not self.motor:
            c.arrived_at = c.arrived_at or now
        if manual:
            self.command = None
        return manual

    def at_rest(self, now: float, stable: float = 15.0) -> bool:
        """Not moving: motor idle, no own command under way and no position change for a while."""
        return not self.motor and not self.active(now) and now - self.last_change >= stable


@dataclass
class ManualPause:
    """The pause after a manual action: until the next phase, for a time, or not at all."""

    since: float | None = None
    until: float | None = None
    until_next_phase: bool = False
    phase: str | None = None
    source: str = ""

    @property
    def on(self) -> bool:
        return self.since is not None

    def start(self, now: float, mode: str, duration_min: float, phase: str | None, source: str) -> bool:
        if mode == "ignore":
            return False
        self.since, self.source, self.phase = now, source, phase
        self.until_next_phase = mode == "until_next_phase"
        self.until = None if self.until_next_phase else now + duration_min * 60
        return True

    def end(self) -> None:
        self.since = self.until = self.phase = None
        self.until_next_phase = False
        self.source = ""

    def still(self, now: float, phase: str | None) -> bool:
        """Whether the pause still applies; ends it when its time or phase is over."""
        if not self.on:
            return False
        if (self.until is not None and now >= self.until) or (self.until_next_phase and phase != self.phase):
            self.end()
        return self.on

    def to_dict(self) -> dict:
        return {
            "since": self.since,
            "until": self.until,
            "until_next_phase": self.until_next_phase,
            "phase": self.phase,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> ManualPause:
        return cls(**data) if data else cls()


def matches(position: int | None, wanted: int | None) -> bool:
    return position is not None and wanted is not None and abs(position - wanted) <= MATCH


class ManualPauseRule:
    """While paused: leave the shutter where it is (final; only safety comes first)."""

    priority = 20
    name = "manual"
    why = None

    def __init__(self, pause: ManualPause, phase_of) -> None:
        self.pause = pause
        self.phase_of = phase_of  # callable(now) -> phase name

    def propose(self, ctx: ShutterContext) -> Decision | None:
        if self.pause.still(ctx.inputs.now, self.phase_of(ctx.inputs.now)):
            return Decision(None, Reason.MANUAL, final=True)
        self.why = ("no_pause", {})
        return None
