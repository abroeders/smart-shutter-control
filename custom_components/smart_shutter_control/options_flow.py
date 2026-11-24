"""The options flow of the base controller."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.helpers import selector

from .const import (
    CONF_WIND_GUST,
    CONF_WIND_SPEED,
    DEFAULT_OPTIONS,
    LANGUAGES,
    OPT_CLOSE_ABOVE,
    OPT_CLOSE_BELOW,
    OPT_CLOSE_DELAY,
    OPT_FROST_LIMIT,
    OPT_FROST_RELEASE,
    OPT_HEAT_OUTDOOR,
    OPT_HEAT_ROOM,
    OPT_HOLIDAY_CALENDAR,
    OPT_HOLIDAYS_DISABLED,
    OPT_HOLIDAYS_EXCLUDED,
    OPT_HOLIDAYS_EXTRA,
    OPT_HOT_DAY,
    OPT_LANGUAGE,
    OPT_MAX_INCIDENCE,
    OPT_OPEN_DELAY,
    OPT_SCHEDULE,
    OPT_STORM_GUST_LIMIT,
    OPT_STORM_LIMIT,
    OPT_STORM_RELEASE,
    OPT_STORM_WIND_LIMIT,
    OPT_SUNNY_THRESHOLD,
    OPT_WEEKEND_DAYS,
    OPT_WINTER_LIMIT,
)
from .core.schedule import DEFAULT_SCHEDULE, HolidayCalendar, merged, parse_holidays, weekend_set
from .flow_common import (
    _number,
    _shown_form,
    _stored_input,
    _with_defaults,
    schedule_fields,
)
from .providers import read_calendar
from .recorder_stats import _max_30_days


def _holiday_calendar(choice: dict[str, Any], values: dict[str, Any], calendar_days: dict) -> HolidayCalendar:
    """The holiday calendar of the weekend days, the extra and excluded dates and the calendar's days."""
    return HolidayCalendar(
        weekend_set(choice.get(OPT_WEEKEND_DAYS)),
        parse_holidays(values.get(OPT_HOLIDAYS_EXTRA))[0],
        parse_holidays(values.get(OPT_HOLIDAYS_EXCLUDED))[0],
        from_calendar=calendar_days,
        disabled=frozenset(values.get(OPT_HOLIDAYS_DISABLED) or []),
    )


def _holiday_listing(calendar: HolidayCalendar) -> str:
    """The holidays of this year, one per line: date and name."""
    from homeassistant.util import dt as dt_util

    year = dt_util.now().year
    return "\n".join(f"{d.strftime('%d-%m-%Y')} {name}".strip() for d, name in calendar.listing(year))


def _disable_field(calendar: HolidayCalendar, current: dict[str, Any]) -> dict:
    """Check boxes for the holidays of the calendar; a checked one is ignored by the schedules."""
    names = calendar.calendar_names()
    disabled = list(current.get(OPT_HOLIDAYS_DISABLED) or [])
    options: list[selector.SelectOptionDict] = [
        {"value": n, "label": f"{n} ({d.strftime('%d-%m-%Y')})"} for n, d in names
    ]
    options += [{"value": n, "label": n} for n in disabled if n not in {o["value"] for o in options}]
    if not options:
        return {}
    return {
        vol.Optional(OPT_HOLIDAYS_DISABLED, default=disabled): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=options, multiple=True, mode=selector.SelectSelectorMode.LIST
            )
        )
    }


class SmartShutterControlOptionsFlow(OptionsFlow):
    """One page per subject; later issues add their pages to the menu."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="init", menu_options=["schedule", "holidays", "sun", "storm", "winter", "language"]
        )

    async def async_step_language(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**DEFAULT_OPTIONS, **self.config_entry.options}
        if user_input is not None:
            return self.async_create_entry(data={**current, **user_input})
        schema = {
            vol.Required(OPT_LANGUAGE): selector.SelectSelector(
                selector.SelectSelectorConfig(options=LANGUAGES, translation_key="language")
            )
        }
        return self.async_show_form(step_id="language", data_schema=_with_defaults(schema, current))

    async def async_step_winter(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**DEFAULT_OPTIONS, **self.config_entry.options}
        schema = {vol.Required(OPT_WINTER_LIMIT): _number(0, 25, 0.5, "°C")}
        if user_input is not None:
            return self.async_create_entry(
                data={**current, **_stored_input(self.hass, schema, user_input, current)}
            )
        return self.async_show_form(step_id="winter", data_schema=_shown_form(self.hass, schema, current))

    async def async_step_schedule(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**DEFAULT_OPTIONS, **self.config_entry.options}
        base = merged(current.get(OPT_SCHEDULE), None)
        fields = schedule_fields(base=True)
        if user_input is not None:
            user_input = _stored_input(self.hass, fields, user_input, base)
            schedule = {k: user_input.get(k) for k in DEFAULT_SCHEDULE}
            return self.async_create_entry(data={**current, OPT_SCHEDULE: schedule})
        return self.async_show_form(step_id="schedule", data_schema=_shown_form(self.hass, fields, base))

    async def async_step_holidays(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Step 1: the calendar and the weekend days. The holidays of that calendar follow on step 2."""
        current = {**DEFAULT_OPTIONS, **self.config_entry.options}
        if user_input is not None:
            self._holiday_choice = {
                OPT_HOLIDAY_CALENDAR: user_input.get(OPT_HOLIDAY_CALENDAR),
                OPT_WEEKEND_DAYS: user_input.get(OPT_WEEKEND_DAYS) or ["sat", "sun"],
            }
            entity_id = user_input.get(OPT_HOLIDAY_CALENDAR)
            self._calendar_days = (await read_calendar(self.hass, entity_id) or {}) if entity_id else {}
            return await self.async_step_holiday_days()
        values = {OPT_WEEKEND_DAYS: ["sat", "sun"], **current}
        schema = {
            vol.Optional(OPT_HOLIDAY_CALENDAR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="calendar")
            ),
            vol.Required(OPT_WEEKEND_DAYS): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
                    multiple=True,
                    translation_key="weekday",
                )
            ),
        }
        return self.async_show_form(step_id="holidays", data_schema=_with_defaults(schema, values))

    async def async_step_holiday_days(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Step 2: the holidays of the chosen calendar (to switch off), extra and excluded dates."""
        current = {**DEFAULT_OPTIONS, **self.config_entry.options}
        errors: dict[str, str] = {}
        bad: list[int] = []
        if user_input is not None and self._shown_days:
            for key in (OPT_HOLIDAYS_EXTRA, OPT_HOLIDAYS_EXCLUDED):
                _, wrong = parse_holidays(user_input.get(key))
                if wrong:
                    errors[key] = "bad_dates"
                    bad += wrong
            if not errors:
                data = {**current, **self._holiday_choice}
                for key in (OPT_HOLIDAYS_EXTRA, OPT_HOLIDAYS_EXCLUDED):
                    data[key] = user_input.get(key)  # cleared fields stay cleared
                data[OPT_HOLIDAYS_DISABLED] = list(user_input.get(OPT_HOLIDAYS_DISABLED) or [])
                return self.async_create_entry(data=data)
        self._shown_days = True
        values = {**current, **(user_input or {})}
        calendar = _holiday_calendar(self._holiday_choice, values, self._calendar_days)
        schema = {
            **_disable_field(calendar, values),
            vol.Optional(OPT_HOLIDAYS_EXTRA): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Optional(OPT_HOLIDAYS_EXCLUDED): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
        }
        listing = _holiday_listing(calendar)
        return self.async_show_form(
            step_id="holiday_days",
            data_schema=_with_defaults(schema, values),
            errors=errors,
            description_placeholders={
                "lines": ", ".join(map(str, bad)) or "–",
                "list": listing or "–",
                "count": str(len(self._calendar_days)),
            },
        )

    _holiday_choice: dict[str, Any] = {}
    _calendar_days: dict = {}
    _shown_days = False

    async def async_step_sun(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**DEFAULT_OPTIONS, **self.config_entry.options}
        schema = {
            vol.Required(OPT_SUNNY_THRESHOLD): _number(10, 100, 5, "%"),
            vol.Required(OPT_MAX_INCIDENCE): _number(30, 90, 1, "°"),
            vol.Required(OPT_HEAT_OUTDOOR): _number(-10, 40, 0.5, "°C"),
            vol.Required(OPT_HEAT_ROOM): _number(10, 35, 0.5, "°C"),
            vol.Optional(OPT_HOT_DAY): _number(15, 45, 0.5, "°C"),
            vol.Required(OPT_CLOSE_DELAY): _number(0, 60, 1, "min"),
            vol.Required(OPT_OPEN_DELAY): _number(0, 120, 1, "min"),
        }
        if user_input is not None:
            user_input = _stored_input(self.hass, schema, user_input, current)
            # an emptied "hot day from" switches it off: keep None, not the old value (#50)
            return self.async_create_entry(data={**current, OPT_HOT_DAY: None, **user_input})
        return self.async_show_form(step_id="sun", data_schema=_shown_form(self.hass, schema, current))

    async def async_step_storm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**DEFAULT_OPTIONS, **self.config_entry.options}
        if OPT_STORM_LIMIT in current and OPT_STORM_GUST_LIMIT not in self.config_entry.options:
            current[OPT_STORM_GUST_LIMIT] = current[OPT_STORM_LIMIT]
        schema = {
            vol.Optional(OPT_STORM_WIND_LIMIT): _number(10, 200, 1, "km/h"),
            vol.Optional(OPT_STORM_GUST_LIMIT): _number(10, 250, 1, "km/h"),
            vol.Required(OPT_STORM_RELEASE): _number(1, 180, 1, "min"),
            vol.Required(OPT_FROST_LIMIT): _number(-20, 10, 0.5, "°C"),
            vol.Required(OPT_FROST_RELEASE): _number(0, 720, 5, "min"),
            vol.Optional(OPT_CLOSE_ABOVE): _number(15, 50, 0.5, "°C"),
            vol.Optional(OPT_CLOSE_BELOW): _number(-30, 10, 0.5, "°C"),
        }
        if user_input is not None:
            user_input = _stored_input(self.hass, schema, user_input, current)
            data = {**current, **user_input}
            for key in (OPT_STORM_WIND_LIMIT, OPT_STORM_GUST_LIMIT, OPT_CLOSE_ABOVE, OPT_CLOSE_BELOW):
                data[key] = user_input.get(key)  # empty = off
            data.pop(OPT_STORM_LIMIT, None)
            return self.async_create_entry(data=data)
        sources = self.config_entry.data
        return self.async_show_form(
            step_id="storm",
            data_schema=_shown_form(self.hass, schema, current),
            description_placeholders={
                "wind_max": await _max_30_days(self.hass, sources.get(CONF_WIND_SPEED), wind=True),
                "gust_max": await _max_30_days(self.hass, sources.get(CONF_WIND_GUST), wind=True),
            },
        )
