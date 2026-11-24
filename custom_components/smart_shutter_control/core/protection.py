"""The delayed on/off state shared by heat and glare protection (#95)."""

from __future__ import annotations

from enum import StrEnum


class Phase(StrEnum):
    OPEN = "open"
    PENDING = "pending"  # conditions met, waiting for close_delay
    SHADING = "shading"
    LEAVING = "leaving"  # conditions gone, waiting for open_delay


class ProtectionState:
    """OPEN → PENDING → SHADING → LEAVING → OPEN, with a delay before closing and before opening.

    The first step after a (re)start goes to SHADING at once when the conditions already hold, so the
    shutter does not open meanwhile. `gone` skips the open delay: the sun has left the window.
    """

    def __init__(self) -> None:
        self.phase = Phase.OPEN
        self.since = 0.0
        self.started = False

    @property
    def active(self) -> bool:
        return self.phase in (Phase.SHADING, Phase.LEAVING)

    def _go(self, phase: Phase, now: float) -> None:
        if phase is not self.phase:
            self.phase, self.since = phase, now

    def reset(self) -> None:
        self.phase = Phase.OPEN

    def step(self, wanted: bool, gone: bool, now: float, close_delay: float, open_delay: float) -> Phase:
        if self.phase is Phase.OPEN and wanted:
            self._go(Phase.SHADING if not self.started else Phase.PENDING, now)
        self.started = True
        if self.phase is Phase.PENDING:
            if not wanted:
                self._go(Phase.OPEN, now)
            elif now - self.since >= close_delay:
                self._go(Phase.SHADING, now)
        if self.phase is Phase.SHADING and not wanted:
            self._go(Phase.LEAVING, now)
        if self.phase is Phase.LEAVING:
            if wanted:
                self._go(Phase.SHADING, now)
            elif gone or now - self.since >= open_delay:
                self._go(Phase.OPEN, now)
        return self.phase

    def remaining(self, now: float, delay: float) -> int:
        """Seconds left of a delay that started when the current phase began."""
        return round(delay - (now - self.since))
