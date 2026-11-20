"""Limits that apply to every automatic position, whatever rule asked for it."""

from __future__ import annotations


class PositionLimiter:
    """Never above the maximum position; in a storm only fully open or fully closed (#6)."""

    def limit(self, target: int, max_position: int, storm: bool = False) -> int:
        target = max(0, min(100, int(round(target))))
        if storm:
            if max_position < 100:
                return 0
            return 100 if target >= 50 else 0
        return min(target, max(0, min(100, max_position)))
