"""Did a move arrive? (#48) After a command: wait until it is due, judge, retry once, then report it stuck.

Pure: no Home Assistant.
"""

from __future__ import annotations

from enum import StrEnum

MATCH = 2  # % : within this of the target counts as arrived
EARLIEST = 10.0  # s : a module needs a moment to start; a motor still off after this never got the command
DEFAULT_TRAVEL = 180.0  # s : the deadline when the travel time is not known


class State(StrEnum):
    IDLE = "idle"
    WAITING = "waiting"  # the first command
    RETRYING = "retrying"  # the same command a second time
    STUCK = "stuck"


class Verdict(StrEnum):
    ARRIVED = "arrived"
    RETRY = "retry"
    STUCK = "stuck"


def deadline_for(travel: float | None) -> float:
    """Seconds after a command by which a move is due at the latest."""
    return travel * 1.5 + 30 if travel else DEFAULT_TRAVEL


class ArrivalCheck:
    def __init__(self, travel: float | None = None) -> None:
        self.deadline = deadline_for(travel)
        self.state = State.IDLE
        self.target: int | None = None
        self.at = 0.0

    @property
    def active(self) -> bool:
        return self.state in (State.WAITING, State.RETRYING)

    def sent(self, target: int, now: float) -> None:
        """A new command: check it from the start (a retry of the same target keeps RETRYING)."""
        if not (self.state is State.RETRYING and target == self.target):
            self.state = State.WAITING
        self.target, self.at = target, now

    def cancel(self) -> None:
        """A manual move or the calibration assistant: nothing to check (a stuck shutter stays stuck)."""
        if self.active:
            self.state = State.IDLE

    def due(self, motor_running: bool | None, now: float) -> bool:
        if not self.active:
            return False
        elapsed = now - self.at
        if elapsed >= self.deadline:
            return True
        if motor_running is None:  # no power sensor: only the deadline
            return False
        return not motor_running and elapsed >= EARLIEST

    def judge(self, position: int | None) -> Verdict:
        """The module's position when due; RETRY means: send the target again (and call sent)."""
        if position is not None and self.target is not None and abs(position - self.target) <= MATCH:
            self.state = State.IDLE
            return Verdict.ARRIVED
        if self.state is State.WAITING:
            self.state = State.RETRYING
            return Verdict.RETRY
        self.state = State.STUCK
        return Verdict.STUCK
