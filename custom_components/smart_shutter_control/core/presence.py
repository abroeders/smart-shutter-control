"""Away and holiday (#51): who is home, when the house counts as away, and the random shift of the schedule
times on holiday (presence simulation). No Home Assistant imports."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date

UNKNOWN = ("unknown", "unavailable", "")


def is_home(domain: str, state: str | None) -> bool:
    """Whether the presence entity says somebody is home; an unknown state counts as home."""
    if state is None or state in UNKNOWN:
        return True
    if domain == "zone":
        try:
            return float(state) > 0
        except ValueError:
            return True
    if domain in ("person", "device_tracker"):
        return state == "home"
    if domain == "group":
        return state in ("home", "on")
    return state == "on"  # binary_sensor


@dataclass
class AwayState:
    """Away once nobody has been home for the delay without a break; home again at once; holiday is away."""

    nobody_since: float | None = None
    away_since: float | None = None

    def step(self, home: bool, holiday: bool, now: float, delay: float) -> bool:
        if home:
            self.nobody_since = None
        elif self.nobody_since is None:
            self.nobody_since = now
        away = holiday or (self.nobody_since is not None and now - self.nobody_since >= delay)
        if not away:
            self.away_since = None
        elif self.away_since is None:
            self.away_since = now
        return away

    def remaining(self, now: float, delay: float) -> float | None:
        """Seconds until nobody home counts as away; None when nobody is waiting for it."""
        if self.nobody_since is None or self.away_since is not None:
            return None
        return max(0.0, self.nobody_since + delay - now)


class ScheduleShift:
    """Strategy for the schedule times: no shift (the default)."""

    def morning(self, day: date) -> int:
        return 0

    def evening(self, day: date) -> int:
        return 0


class NoShift(ScheduleShift):
    pass


class RandomShift(ScheduleShift):
    """A random shift in whole minutes within ±`minutes`, one for the morning and one for the evening, the
    same for the same seed, shutter and day (so a restart does not move a shutter twice)."""

    def __init__(self, seed: int, shutter_id: str, minutes: int) -> None:
        self.seed, self.shutter_id, self.minutes = seed, shutter_id, max(0, int(minutes))

    def _draws(self, day: date) -> tuple[int, int]:
        rng = random.Random(f"{self.seed}:{self.shutter_id}:{day.isoformat()}")  # noqa: S311 not for security
        return rng.randint(-self.minutes, self.minutes), rng.randint(-self.minutes, self.minutes)

    def morning(self, day: date) -> int:
        return self._draws(day)[0]

    def evening(self, day: date) -> int:
        return self._draws(day)[1]
