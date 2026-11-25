"""Locks set by an automation (#52): hold a shutter or force it open or closed, for a while or until ended.
No Home Assistant imports."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .model import Decision, Reason, ShutterContext


class LockMode(StrEnum):
    NONE = "none"
    HOLD = "hold"  # the controller does not move the shutter
    FORCE_OPEN = "force_open"  # fully open, also above the maximum position
    FORCE_CLOSED = "force_closed"


POSITIONS = {LockMode.FORCE_OPEN: 100, LockMode.FORCE_CLOSED: 0}


@dataclass
class Lock:
    """The lock of one shutter (repository: to/from dict in the runtime store)."""

    mode: LockMode = LockMode.NONE
    until: float | None = None  # end time (epoch seconds); None: until it is ended

    @property
    def on(self) -> bool:
        return self.mode is not LockMode.NONE

    def set(self, mode: LockMode | str, now: float, duration_s: float | None = None) -> None:
        self.mode = LockMode(mode)
        self.until = now + duration_s if self.on and duration_s is not None else None

    def end(self) -> None:
        self.mode, self.until = LockMode.NONE, None

    def still(self, now: float) -> bool:
        """Whether the lock still applies; ends it when its time is over."""
        if self.on and self.until is not None and now >= self.until:
            self.end()
        return self.on

    def to_dict(self) -> dict:
        return {"mode": self.mode.value, "until": self.until}

    @classmethod
    def from_dict(cls, data: dict | None) -> Lock:
        if not data:
            return cls()
        try:
            return cls(LockMode(data.get("mode", LockMode.NONE)), data.get("until"))
        except ValueError:
            return cls()


class LockRule:
    """While locked: the lock decides (final). Storm and frost come first; the door floors apply after."""

    priority = 12
    name = "lock"
    why: tuple[str, dict] | None = None

    def __init__(self, lock: Lock) -> None:
        self.lock = lock

    def propose(self, ctx: ShutterContext) -> Decision | None:
        if not self.lock.still(ctx.inputs.now):
            self.why = ("unlocked", {})
            return None
        self.why = ("locked", {"mode": self.lock.mode.value})
        return Decision(POSITIONS.get(self.lock.mode), Reason.LOCKED, final=True)
