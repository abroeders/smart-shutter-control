"""Window and door contacts (#49): never lock someone out, leave a gap for a tilted window.

The guard gives a floor: automatic control keeps the shutter at least this high. Pure: no Home Assistant.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import Reason

HOLD = 60.0  # s: the floor stays this long after the contact closes
Target = tuple[str, int]  # ("real", position) or ("module", module position: the slit)


@dataclass(frozen=True)
class Floor:
    reason: str  # lockout | ventilation
    target: Target
    safety: bool  # lockout: also above the maximum position and in a storm


@dataclass
class Contact:
    on: bool = False
    off_since: float | None = None  # when it closed; the floor holds until HOLD later

    def update(self, on: bool | None, now: float) -> bool:
        """The new state (None: unavailable, keep the last one); true when it has just opened."""
        if on is None or on == self.on:
            return False
        self.on = on
        self.off_since = None if on else now
        return on

    def holds(self, now: float) -> bool:
        return self.on or (self.off_since is not None and now - self.off_since < HOLD)

    def release_at(self) -> float | None:
        return None if self.on or self.off_since is None else self.off_since + HOLD


class OpeningGuard:
    def __init__(self, lockout: int = 100, ventilation: int | None = None) -> None:
        self.lockout = lockout
        self.ventilation = ventilation  # real %, or None: the slit
        self.opened = Contact()
        self.tilted = Contact()

    def update(self, opened: bool | None, tilted: bool | None, now: float) -> bool:
        """True when the door or window has just opened (a manual pause ends then)."""
        just_opened = self.opened.update(opened, now)
        self.tilted.update(tilted, now)
        return just_opened

    def floor(self, now: float, slit_module: int, max_position: int) -> Floor | None:
        if self.opened.holds(now):
            return Floor(Reason.LOCKOUT, ("real", self.lockout), True)
        if self.tilted.holds(now):
            if self.ventilation is None:
                return Floor(Reason.VENTILATION, ("module", slit_module), False)
            return Floor(Reason.VENTILATION, ("real", min(self.ventilation, max_position)), False)
        return None

    def release_at(self) -> float | None:
        """When a closed contact's floor ends, for one more evaluation then."""
        times = [t for t in (self.opened.release_at(), self.tilted.release_at()) if t is not None]
        return min(times) if times else None


def rank(target: Target) -> float:
    """Height for comparing: the slit lies just above fully closed and below every open position."""
    kind, value = target
    if kind == "module":
        return 0.5
    return float(value)


def raise_to(
    target: Target | None, current: Target | None, floor: Floor | None, storm: bool
) -> Target | None:
    """The floor when the target (or, without one, the current position) is below it; else the target.

    In a storm only the ends exist: the lockout floor is fully open there, and ventilation gives way."""
    if floor is None:
        return target
    if storm:
        if not floor.safety:
            return target
        floor = Floor(floor.reason, ("real", 100), True)
    base = target if target is not None else current
    if base is None or rank(base) >= rank(floor.target):
        return target
    return floor.target
