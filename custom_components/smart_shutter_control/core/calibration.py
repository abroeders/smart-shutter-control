"""Converting between the real position of a shutter and the position its module works with (#10)."""

from __future__ import annotations

from typing import Protocol

from .model import Direction


class Calibration(Protocol):
    def to_module(self, position: int, direction: Direction) -> int:
        """Module position to send for a real position, reached moving in this direction."""

    def from_module(self, position: int, direction: Direction) -> int:
        """Real position for a module position, reached moving in this direction."""


class IdentityCalibration:
    """No calibration yet: the module position is the real position."""

    def to_module(self, position: int, direction: Direction) -> int:
        return position

    def from_module(self, position: int, direction: Direction) -> int:
        return position
