"""Today's maximum temperature from a daily weather forecast (#50). Pure: no Home Assistant."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, tzinfo
from typing import Any


def today_max(forecast: Iterable[Mapping[str, Any]], today: date, zone: tzinfo) -> float | None:
    """The `temperature` of the entry whose date, in local time, is today."""
    for entry in forecast:
        try:
            moment = datetime.fromisoformat(str(entry["datetime"]))
            value = float(entry["temperature"])
        except (KeyError, TypeError, ValueError):
            continue
        local = moment.astimezone(zone) if moment.tzinfo else moment
        if local.date() == today:
            return value
    return None


@dataclass
class ForecastMaximum:
    """The last known maximum for a day; a value from another day says nothing about today."""

    day: date | None = None
    value: float | None = None

    def update(self, value: float | None, today: date) -> None:
        if value is not None:
            self.day, self.value = today, value
        elif self.day != today:
            self.day, self.value = None, None  # a failed call keeps today's value, not yesterday's

    def today(self, today: date) -> float | None:
        return self.value if self.day == today else None
