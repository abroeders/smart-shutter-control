"""Providers for the base controller: today's forecast maximum and the holiday calendar, each read from a
Home Assistant entity and kept up to date by its own listeners (#98)."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
    async_track_time_interval,
)
from homeassistant.helpers.start import async_at_started
from homeassistant.util import dt as dt_util

from . import units
from .const import (
    FORECAST_SECONDS,
    OPT_HOLIDAY_CALENDAR,
    OPT_HOLIDAYS_DISABLED,
    OPT_HOLIDAYS_EXCLUDED,
    OPT_HOLIDAYS_EXTRA,
    OPT_WEEKEND_DAYS,
)
from .core.forecast import ForecastMaximum, today_max
from .core.schedule import HolidayCalendar, parse_holidays, weekend_set

_LOGGER = logging.getLogger(__name__)


def _unavailable(state: Any) -> bool:
    return state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN)


async def read_calendar(hass: HomeAssistant, entity_id: str) -> dict[date, str] | None:
    """Holidays (date → name) of the coming 400 days from a calendar entity; None when it cannot be read."""
    start = dt_util.now()
    try:
        response = await hass.services.async_call(
            "calendar",
            "get_events",
            {
                "entity_id": entity_id,
                "start_date_time": start.isoformat(),
                "end_date_time": (start + timedelta(days=400)).isoformat(),
            },
            blocking=True,
            return_response=True,
        )
    except (HomeAssistantError, ValueError) as err:
        _LOGGER.warning("Could not read holidays from %s: %s", entity_id, err)
        return None
    days = {}
    events: dict[str, Any] = response or {}
    for event in events.get(entity_id, {}).get("events", []):
        day = dt_util.parse_date(str(event.get("start", ""))[:10])
        if day is not None:
            days[day] = str(event.get("summary") or "")
    return days


class ForecastProvider:
    """Today's maximum temperature from the weather entity's daily forecast (#50)."""

    def __init__(self, hass: HomeAssistant, entity_id: str | None) -> None:
        self.hass = hass
        self.entity_id = entity_id
        self.maximum = ForecastMaximum()

    @property
    def value(self) -> float | None:
        """Today's forecast maximum in °C; None without one for today."""
        return self.maximum.today(dt_util.now().date())

    @property
    def day(self) -> date | None:
        return self.maximum.day

    async def async_refresh(self) -> None:
        """Read the daily forecast; a failed call keeps today's value."""
        today = dt_util.now().date()
        value = None
        weather = self.hass.states.get(self.entity_id) if self.entity_id else None
        if weather is not None:
            try:
                response = await self.hass.services.async_call(
                    "weather",
                    "get_forecasts",
                    {"entity_id": self.entity_id, "type": "daily"},
                    blocking=True,
                    return_response=True,
                )
            except HomeAssistantError as err:
                _LOGGER.debug("No daily forecast from %s: %s", self.entity_id, err)
            else:
                forecasts: dict[str, Any] = response or {}
                forecast = forecasts.get(self.entity_id or "", {}).get("forecast") or []
                value = today_max(forecast, today, dt_util.get_default_time_zone())
                if value is not None:  # in the weather entity's unit (#64)
                    value = units.to_celsius(value, weather.attributes.get("temperature_unit"))
        self.maximum.update(value, today)

    def track(self, on_update: Callable[[], None]) -> list[CALLBACK_TYPE]:
        """Refresh periodically, and once the weather entity is there; `on_update` after the latter."""

        async def _refresh_and_update() -> None:
            await self.async_refresh()
            on_update()

        async def _on_interval(_now: datetime) -> None:
            await self.async_refresh()

        async def _on_started(_hass: HomeAssistant) -> None:
            await _refresh_and_update()

        async def _on_weather(event: Event[EventStateChangedData]) -> None:
            """The weather entity appeared or became available again: read the forecast now (#67)."""
            if _unavailable(event.data.get("old_state")) and not _unavailable(event.data.get("new_state")):
                await _refresh_and_update()

        unsubs = [async_track_time_interval(self.hass, _on_interval, timedelta(seconds=FORECAST_SECONDS))]
        if self.entity_id:
            # the weather integration may start after this one: read the forecast once it is there (#67)
            unsubs.append(async_track_state_change_event(self.hass, [self.entity_id], _on_weather))
            unsubs.append(async_at_started(self.hass, _on_started))
        return unsubs


class HolidayProvider:
    """The free days for the schedules: weekend days, extra and excluded dates from the options, and the
    holidays of a calendar entity, read again every night."""

    def __init__(self, hass: HomeAssistant, options: Mapping[str, Any]) -> None:
        self.hass = hass
        self.entity_id: str | None = options.get(OPT_HOLIDAY_CALENDAR) or None
        extra, _ = parse_holidays(options.get(OPT_HOLIDAYS_EXTRA))
        excluded, _ = parse_holidays(options.get(OPT_HOLIDAYS_EXCLUDED))
        self.calendar = HolidayCalendar(
            weekend_set(options.get(OPT_WEEKEND_DAYS)),
            extra,
            excluded,
            disabled=frozenset(options.get(OPT_HOLIDAYS_DISABLED) or []),
        )

    async def async_refresh(self) -> None:
        """Read the public holidays of the coming 400 days from the calendar entity, if one is set."""
        if not self.entity_id:
            self.calendar.from_calendar = {}
            return
        days = await read_calendar(self.hass, self.entity_id)
        if days is not None:
            self.calendar.from_calendar = days

    def track(self, on_update: Callable[[], None]) -> list[CALLBACK_TYPE]:
        """Refresh every night, and once the calendar entity is there; `on_update` after the latter."""

        async def _on_midnight(_now: datetime) -> None:
            await self.async_refresh()

        async def _on_started(_hass: HomeAssistant) -> None:
            await self.async_refresh()

        async def _on_calendar(event: Event[EventStateChangedData]) -> None:
            if _unavailable(event.data.get("old_state")) or not self.calendar.from_calendar:
                await self.async_refresh()
                on_update()

        unsubs = [async_track_time_change(self.hass, _on_midnight, hour=0, minute=5, second=0)]
        if self.entity_id:
            # the calendar's integration may start after this one: read it once it is there
            unsubs.append(async_track_state_change_event(self.hass, [self.entity_id], _on_calendar))
            unsubs.append(async_at_started(self.hass, _on_started))
        return unsubs
