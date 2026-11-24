"""Shared form helpers and constants of the config, options and subentry flows."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.helpers import selector

from .const import (
    CONF_LIGHT,
    CONF_LUX_LIMIT,
    CONF_OUTDOOR,
    CONF_PV_PEAK,
    CONF_PV_POWER,
    CONF_SUN_DEPTH,
    CONF_SUN_SOURCE,
    CONF_WEATHER,
    CONF_WIND_GUST,
    CONF_WIND_SPEED,
    CONF_WINDOW_HEIGHT,
    CONF_WINDOW_SILL,
    DEFAULT_LUX_LIMIT,
    OPT_CLOSE_ABOVE,
    OPT_CLOSE_BELOW,
    OPT_FROST_LIMIT,
    OPT_HEAT_OUTDOOR,
    OPT_HEAT_ROOM,
    OPT_HOT_DAY,
    OPT_STORM_GUST_LIMIT,
    OPT_STORM_WIND_LIMIT,
    OPT_WINTER_LIMIT,
    SUN_SOURCES,
)
from .units import DisplayUnit, length_unit, speed_unit, temperature_unit


def _sensor(device_class: str | None = None, multiple: bool = False) -> selector.EntitySelector:
    config = selector.EntitySelectorConfig(domain="sensor", multiple=multiple)
    if device_class:
        config["device_class"] = device_class
    return selector.EntitySelector(config)


def _number(low: float, high: float, step: float, unit: str | None = None) -> selector.NumberSelector:
    config = selector.NumberSelectorConfig(min=low, max=high, step=step, mode=selector.NumberSelectorMode.BOX)
    if unit is not None:
        config["unit_of_measurement"] = unit
    return selector.NumberSelector(config)


def _with_defaults(schema: dict, values: dict[str, Any]) -> vol.Schema:
    """Fill the defaults of a schema from the current values (optional keys get a suggested value)."""
    out = {}
    for key, validator in schema.items():
        name = str(key)
        if name in values and values[name] is not None:
            if isinstance(key, vol.Required):
                key = vol.Required(name, default=values[name])
            else:
                key = vol.Optional(name, description={"suggested_value": values[name]})
        out[key] = validator
    return vol.Schema(out)


# settings stored in °C or km/h, shown and entered in the user's unit system (#65)
TEMPERATURE_FIELDS = {
    OPT_HEAT_OUTDOOR,
    OPT_HEAT_ROOM,
    OPT_HOT_DAY,
    OPT_WINTER_LIMIT,
    OPT_FROST_LIMIT,
    OPT_CLOSE_ABOVE,
    OPT_CLOSE_BELOW,
    "winter_closed_below",
}
SPEED_FIELDS = {OPT_STORM_WIND_LIMIT, OPT_STORM_GUST_LIMIT}
# lengths stored in cm or m, shown in inches or feet with US customary units (#71): stored unit, shown step
LENGTH_FIELDS = {
    CONF_WINDOW_SILL: ("cm", 1),
    CONF_WINDOW_HEIGHT: ("cm", 1),
    CONF_SUN_DEPTH: ("m", 0.5),
    "window_height_cm": ("cm", 1),  # the calibration assistant's window height (#84)
}


def _display_units(hass, schema: dict) -> dict[str, DisplayUnit]:
    out = {}
    for key in schema:
        name = str(key)
        if name in TEMPERATURE_FIELDS:
            out[name] = temperature_unit(hass)
        elif name in SPEED_FIELDS:
            out[name] = speed_unit(hass)
        elif name in LENGTH_FIELDS:
            out[name] = length_unit(hass, *LENGTH_FIELDS[name])
    return out


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _shown_form(hass, schema: dict, values: dict[str, Any]) -> vol.Schema:
    """`_with_defaults` with the temperatures, wind speeds and lengths in the user's units (#65, #71)."""
    shown_units = _display_units(hass, schema)
    out = {}
    for key, validator in schema.items():
        unit = shown_units.get(str(key))
        if unit is not None:
            config = validator.config
            validator = selector.NumberSelector(
                selector.NumberSelectorConfig(
                    **{**config, **unit.selector_config(config["min"], config["max"], config["step"])}
                )
            )
        out[key] = validator
    shown = {
        key: shown_units[key].shown(value) if key in shown_units and _is_number(value) else value
        for key, value in values.items()
    }
    return _with_defaults(out, shown)


def _stored_input(hass, schema: dict, user_input: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    """A form's input with the temperatures, wind speeds and lengths back in °C, km/h, cm and m (#65, #71)."""
    shown_units = _display_units(hass, schema)
    return {
        key: shown_units[key].stored(value, previous.get(key))
        if key in shown_units and _is_number(value)
        else value
        for key, value in user_input.items()
    }


def _time() -> selector.TimeSelector:
    return selector.TimeSelector()


def _phase_switch(base: bool) -> selector.Selector:
    """On/off in the base schedule; inherit/on/off for a shutter."""
    if base:
        return selector.BooleanSelector()
    return selector.SelectSelector(
        selector.SelectSelectorConfig(options=["inherit", "on", "off"], translation_key="phase_switch")
    )


INHERIT_MANUAL = ["inherit", "until_next_phase", "for_duration", "ignore"]
# override fields with a choice: they show "inherit" when the shutter follows the base schedule
INHERIT_CHOICES = (
    "slit_phase",
    "not_before_sunrise",
    "dusk_phase",
    "winter",
    "storm_position",
    "manual_mode",
)


def schedule_fields(base: bool) -> dict:
    """The schedule settings; for a shutter every field is optional (empty = the base value)."""
    key = vol.Required if base else vol.Optional
    return {
        key("weekday_slit"): _time(),
        key("weekday_open"): _time(),
        key("weekend_slit"): _time(),
        key("weekend_open"): _time(),
        key("slit_phase"): _phase_switch(base),
        key("not_before_sunrise"): _phase_switch(base),
        key("sunrise_offset"): _number(-120, 120, 5, "min"),
        key("dusk_phase"): _phase_switch(base),
        key("dusk_offset"): _number(-120, 120, 5, "min"),
        key("dusk_position"): _number(0, 100, 5, "%"),
        key("close_offset"): _number(-120, 180, 5, "min"),
        vol.Optional("close_earliest"): _time(),
        vol.Optional("close_latest"): _time(),
        key("open_position"): _number(0, 100, 5, "%"),
        key("slit_module"): _number(0, 60, 1, "%"),
        key("sleep_in_until"): _time(),
        key("manual_mode"): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=(INHERIT_MANUAL[1:] if base else INHERIT_MANUAL),
                translation_key="manual_mode",
            )
        ),
        key("manual_duration"): _number(5, 1440, 5, "min"),
        key("winter"): _phase_switch(base),
        vol.Optional("winter_closed_below"): _number(-30, 10, 0.5, "°C"),
        key("storm_position"): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=(["nearest", "open", "closed"] if base else ["inherit", "nearest", "open", "closed"]),
                translation_key="storm_position",
            )
        ),
    }


BASE_WORDS = {
    "nl": {
        True: "aan",
        False: "uit",
        "until_next_phase": "pauze tot de volgende fase",
        "for_duration": "een tijd lang pauze",
        "ignore": "negeren",
        None: "–",
    },
    "en": {
        True: "on",
        False: "off",
        "until_next_phase": "pause until the next phase",
        "for_duration": "pause for a while",
        "ignore": "ignore",
        None: "–",
    },
}
UNITS = {
    "sunrise_offset": " min",
    "dusk_offset": " min",
    "close_offset": " min",
    "manual_duration": " min",
    "dusk_position": " %",
    "open_position": " %",
    "slit_module": " %",
}


def base_placeholders(base: dict[str, Any], language: str | None) -> dict[str, str]:
    """`base_<setting>` = the base schedule's value, readable, for the help text under each field."""
    words = BASE_WORDS.get((language or "en")[:2], BASE_WORDS["en"])
    out = {}
    for key, value in base.items():
        if isinstance(value, bool) or value is None or (isinstance(value, str) and value in words):
            text = words.get(value, str(value))
        elif isinstance(value, str) and value.count(":") >= 1:
            text = value[:5]  # 08:00:00 → 08:00
        elif isinstance(value, float) and value.is_integer():
            text = f"{int(value)}{UNITS.get(key, '')}"
        else:
            text = f"{value}{UNITS.get(key, '')}"
        out[f"base_{key}"] = text
    return out


SOURCES = {
    vol.Required(CONF_OUTDOOR): _sensor("temperature"),
    vol.Optional(CONF_WEATHER): selector.EntitySelector(selector.EntitySelectorConfig(domain="weather")),
    vol.Required(CONF_SUN_SOURCE, default="pv"): selector.SelectSelector(
        selector.SelectSelectorConfig(options=SUN_SOURCES, translation_key="sun_source")
    ),
    vol.Optional(CONF_WIND_SPEED): _sensor("wind_speed"),
    vol.Optional(CONF_WIND_GUST): _sensor("wind_speed"),
}
# the second step: only the fields of the chosen sun source, so PV and light sensors are never both set
SUN_FIELDS: dict[str, dict] = {
    "pv": {
        vol.Required(CONF_PV_POWER): _sensor("power", multiple=True),
        vol.Optional(CONF_PV_PEAK): _number(0.1, 100, 0.1, "kWp"),
    },
    "light": {
        vol.Required(CONF_LIGHT): _sensor("illuminance", multiple=True),
        vol.Required(CONF_LUX_LIMIT, default=DEFAULT_LUX_LIMIT): _number(1000, 150000, 1000, "lx"),
    },
}
SUN_KEYS = (CONF_PV_POWER, CONF_PV_PEAK, CONF_LIGHT, CONF_LUX_LIMIT)
