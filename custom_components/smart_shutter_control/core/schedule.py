"""Schedules (#4): the phases of a shutter's day from a base schedule with per-shutter overrides,
sunrise and sunset, weekends and holidays. No Home Assistant imports.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from functools import lru_cache
from typing import Any
from zoneinfo import ZoneInfo

from .sun import SunPosition

SUN_ALTITUDE = -0.833  # degrees: sunrise and sunset (refraction and the sun's radius)
INHERIT = None  # an override that is absent or None takes the base value
NONE = "none"  # an override that removes a phase (no slit, no dusk)


class Phase(StrEnum):
    NIGHT = "night"
    SLIT = "slit"
    DAY = "day"
    DUSK = "dusk"


# --- settings: base schedule with overrides -----------------------------------------------------
DEFAULT_SCHEDULE: dict[str, Any] = {
    "weekday_slit": "08:00",
    "weekday_open": "08:30",
    "weekend_slit": "10:00",
    "weekend_open": "10:30",
    "slit_phase": True,
    "not_before_sunrise": False,
    "sunrise_offset": 0,  # min
    "dusk_phase": True,
    "dusk_offset": 0,  # min after sunset
    "dusk_position": 35,  # %
    "close_offset": 15,  # min after sunset
    "close_earliest": None,
    "close_latest": None,
    "open_position": 100,  # %
    "slit_module": 20,  # % module position for the slit when the shutter is not calibrated
    "sleep_in_until": "12:00",
    "manual_mode": "until_next_phase",  # until_next_phase, for_duration, ignore
    "manual_duration": 120,  # min
    "storm_position": "nearest",  # nearest, open, closed (#6)
    "winter": True,  # winter mode applies to this shutter (#7)
    "winter_closed_below": -5,  # °C: in winter closed all day at or below this; None = off
}


def merged(base: Mapping[str, Any] | None, overrides: Mapping[str, Any] | None) -> dict[str, Any]:
    """Base values (with defaults), replaced by every override that is set (empty = inherit)."""
    values = {**DEFAULT_SCHEDULE, **{k: v for k, v in (base or {}).items() if v is not None}}
    for key, value in (overrides or {}).items():
        if value is not None and value != "" and value != "inherit":
            values[key] = value
    return values


def overridden(overrides: Mapping[str, Any] | None) -> list[str]:
    return sorted(k for k, v in (overrides or {}).items() if v is not None and v != "" and v != "inherit")


def _time(value: Any) -> time | None:
    if value in (None, "", NONE):
        return None
    if isinstance(value, time):
        return value
    hours, minutes, *rest = (int(x) for x in str(value).split(":"))
    return time(hours, minutes, rest[0] if rest else 0)


def _on(value: Any) -> bool:
    """A phase switch: True/False in the base, on/off/none in an override."""
    return value not in (False, "off", NONE, "false")


# --- sunrise and sunset -------------------------------------------------------------------------
@dataclass(frozen=True)
class SunTimes:
    latitude: float
    longitude: float

    def _elevation(self, moment: datetime) -> float:
        return SunPosition.at(self.latitude, self.longitude, moment.timestamp()).elevation

    def _cross(self, a: datetime, b: datetime, rising: bool) -> datetime | None:
        ea, eb = self._elevation(a) - SUN_ALTITUDE, self._elevation(b) - SUN_ALTITUDE
        if (ea < 0 <= eb) if rising else (ea >= 0 > eb):
            for _ in range(30):
                mid = a + (b - a) / 2
                em = self._elevation(mid) - SUN_ALTITUDE
                if (em < 0) == rising:
                    a = mid
                else:
                    b = mid
            return a + (b - a) / 2
        return None

    def sunrise_sunset(self, day: date, tz: ZoneInfo) -> tuple[datetime | None, datetime | None]:
        return _sun_times(self.latitude, self.longitude, day, str(tz))


@lru_cache(maxsize=64)
def _sun_times(lat: float, lon: float, day: date, tz: str) -> tuple[datetime | None, datetime | None]:
    st = SunTimes(lat, lon)
    zone = ZoneInfo(tz)
    start = datetime.combine(day, time(0), zone)
    hours = [start + timedelta(minutes=30 * i) for i in range(49)]
    rise = set_ = None
    for a, b in zip(hours, hours[1:], strict=False):
        rise = rise or st._cross(a, b, rising=True)
        set_ = set_ or st._cross(a, b, rising=False)
    return rise, set_


# --- holidays -------------------------------------------------------------------------------------
LINE = re.compile(r"^\s*(?:(\d{4})-)?(\d{1,2})-(\d{1,2})\s*(.*)$")


@dataclass(frozen=True)
class HolidayEntry:
    year: int | None  # None: every year
    month: int
    day: int
    name: str = ""

    def matches(self, d: date) -> bool:
        return d.month == self.month and d.day == self.day and (self.year is None or self.year == d.year)


def parse_holidays(text: str | None) -> tuple[list[HolidayEntry], list[int]]:
    """One date per line: `2026-12-24 name` (once) or `12-31 name` (every year). Returns entries and the
    numbers of the lines that could not be read."""
    entries: list[HolidayEntry] = []
    bad: list[int] = []
    for number, line in enumerate((text or "").splitlines(), start=1):
        if not line.strip():
            continue
        m = LINE.match(line)
        try:
            year = int(m.group(1)) if m and m.group(1) else None
            entry = HolidayEntry(year, int(m.group(2)), int(m.group(3)), m.group(4).strip()) if m else None
            if entry is None:
                raise ValueError
            date(year or 2024, entry.month, entry.day)  # valid (2024: a leap year)
            entries.append(entry)
        except (ValueError, AttributeError):
            bad.append(number)
    return entries, bad


@dataclass
class HolidayCalendar:
    """Free days for the schedules: weekend days, holidays from a calendar, extra and excluded dates."""

    weekend_days: frozenset[int] = frozenset({5, 6})  # Monday = 0
    extra: list[HolidayEntry] = field(default_factory=list)
    excluded: list[HolidayEntry] = field(default_factory=list)
    from_calendar: dict[date, str] = field(default_factory=dict)
    disabled: frozenset[str] = frozenset()  # names of calendar holidays that do not count (every year)

    def holiday(self, d: date) -> str | None:
        """The name of the holiday on this date (empty string when it has none), or None."""
        if any(e.matches(d) for e in self.excluded):
            return None
        for e in self.extra:
            if e.matches(d):
                return e.name
        name = self.from_calendar.get(d)
        return None if name is not None and name in self.disabled else name

    def calendar_names(self) -> list[tuple[str, date]]:
        """Each holiday name from the calendar with its next date, in date order (for the options page)."""
        first: dict[str, date] = {}
        for d, name in sorted(self.from_calendar.items()):
            if name and name not in first:
                first[name] = d
        return sorted(((n, d) for n, d in first.items()), key=lambda x: x[1])

    def is_free(self, d: date) -> bool:
        return d.weekday() in self.weekend_days or self.holiday(d) is not None

    def listing(self, year: int) -> list[tuple[date, str]]:
        """All holidays of a year (not the weekend days), for the options page."""
        days = [date(year, 1, 1) + timedelta(days=i) for i in range(366 if year % 4 == 0 else 365)]
        return [(d, self.holiday(d) or "") for d in days if self.holiday(d) is not None]


# --- the day of a shutter ------------------------------------------------------------------------
@dataclass(frozen=True)
class Transition:
    at: datetime
    phase: Phase


class DaySchedule:
    """When each phase starts on a given day, and the phase at any moment."""

    def __init__(
        self, values: Mapping[str, Any], sun: SunTimes, calendar: HolidayCalendar, tz: ZoneInfo
    ) -> None:
        self.values = dict(values)
        self.sun = sun
        self.calendar = calendar
        self.tz = tz

    def transitions(self, day: date) -> list[Transition]:
        v, tz = self.values, self.tz
        free = self.calendar.is_free(day)
        prefix = "weekend" if free else "weekday"
        sunrise, sunset = self.sun.sunrise_sunset(day, tz)

        def at(t: time | None) -> datetime | None:
            return None if t is None else datetime.combine(day, t, tz)

        slit = at(_time(v[f"{prefix}_slit"])) if _on(v["slit_phase"]) else None
        opened = at(_time(v[f"{prefix}_open"]))
        if _on(v["not_before_sunrise"]) and sunrise is not None:
            earliest = sunrise + timedelta(minutes=float(v["sunrise_offset"] or 0))
            slit = max(slit, earliest) if slit else None
            opened = max(opened, earliest) if opened else None
        if sunset is None:  # polar day or night: fall back to the latest close time, or 21:00
            sunset = at(_time(v["close_latest"])) or at(time(21, 0))
        close = sunset + timedelta(minutes=float(v["close_offset"] or 0))
        earliest, latest = at(_time(v["close_earliest"])), at(_time(v["close_latest"]))
        if earliest and close < earliest:
            close = earliest
        if latest and close > latest:
            close = latest
        dusk = sunset + timedelta(minutes=float(v["dusk_offset"] or 0)) if _on(v["dusk_phase"]) else None
        if dusk is not None and dusk >= close:
            dusk = None
        out = []
        if slit is not None and (opened is None or slit < opened):
            out.append(Transition(slit, Phase.SLIT))
        if opened is not None:
            out.append(Transition(opened, Phase.DAY))
        if dusk is not None and (opened is None or dusk > opened):
            out.append(Transition(dusk, Phase.DUSK))
        out.append(Transition(close, Phase.NIGHT))
        return sorted(out, key=lambda t: t.at)

    def phase_at(self, now: datetime) -> Phase:
        local = now.astimezone(self.tz)
        current = Phase.NIGHT
        for t in self.transitions(local.date()):
            if t.at <= local:
                current = t.phase
        return current

    def next_change(self, now: datetime) -> Transition | None:
        local = now.astimezone(self.tz)
        for offset in range(3):
            for t in self.transitions(local.date() + timedelta(days=offset)):
                if t.at > local:
                    return t
        return None

    def target(self, phase: Phase) -> int:
        """Real position for a phase (the slit is handled apart: it is a module position)."""
        if phase is Phase.DAY:
            return int(self.values["open_position"])
        if phase is Phase.DUSK:
            return int(self.values["dusk_position"])
        return 0

    def sleep_in_until(self, now: datetime) -> datetime:
        local = now.astimezone(self.tz)
        return datetime.combine(local.date(), _time(self.values["sleep_in_until"]) or time(12), self.tz)


def weekend_set(days: Iterable[str] | None) -> frozenset[int]:
    names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    return frozenset(names.index(d) for d in (days or ["sat", "sun"]) if d in names)
