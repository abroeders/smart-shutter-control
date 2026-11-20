"""Config flow (base controller), options flow and the subentry flow for a shutter."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.cover import CoverEntityFeature
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.const import ATTR_SUPPORTED_FEATURES, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_AZIMUTH,
    CONF_COVER,
    CONF_MAX_ELEVATION,
    CONF_MAX_POSITION,
    CONF_MIN_ELEVATION,
    CONF_OUTDOOR,
    CONF_PV_FORECAST,
    CONF_PV_PEAK,
    CONF_PV_POWER,
    CONF_ROOM_TEMPERATURE,
    CONF_TILT,
    CONF_WEATHER,
    CONF_WIND_GUST,
    CONF_WIND_SPEED,
    DEFAULT_NAME,
    DEFAULT_OPTIONS,
    DEFAULT_SHUTTER,
    DOMAIN,
    OPT_STORM_LIMIT,
    SUBENTRY_SHUTTER,
)


def _sensor(device_class: str | None = None, multiple: bool = False) -> selector.EntitySelector:
    config: dict[str, Any] = {"domain": "sensor", "multiple": multiple}
    if device_class:
        config["device_class"] = device_class
    return selector.EntitySelector(selector.EntitySelectorConfig(**config))


def _number(low: float, high: float, step: float, unit: str | None = None) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=low, max=high, step=step, unit_of_measurement=unit, mode=selector.NumberSelectorMode.BOX
        )
    )


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


SOURCES = {
    vol.Required(CONF_OUTDOOR): _sensor("temperature"),
    vol.Optional(CONF_WEATHER): selector.EntitySelector(selector.EntitySelectorConfig(domain="weather")),
    vol.Optional(CONF_PV_POWER): _sensor("power", multiple=True),
    vol.Optional(CONF_PV_PEAK): _number(0.1, 100, 0.1, "kWp"),
    vol.Optional(CONF_PV_FORECAST): _sensor("power"),
    vol.Optional(CONF_WIND_SPEED): _sensor("wind_speed"),
    vol.Optional(CONF_WIND_GUST): _sensor("wind_speed"),
}


class SmartShutterControlConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._name = DEFAULT_NAME

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._name = user_input[CONF_NAME]
            return await self.async_step_sources()
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required(CONF_NAME, default=DEFAULT_NAME): str})
        )

    async def async_step_sources(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title=self._name, data=user_input, options=dict(DEFAULT_OPTIONS))
        return self.async_show_form(step_id="sources", data_schema=vol.Schema(SOURCES))

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            return self.async_update_reload_and_abort(entry, data=user_input)
        return self.async_show_form(
            step_id="reconfigure", data_schema=_with_defaults(SOURCES, dict(entry.data))
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SmartShutterControlOptionsFlow()

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        return {SUBENTRY_SHUTTER: ShutterSubentryFlow}


class SmartShutterControlOptionsFlow(OptionsFlow):
    """One page per subject; later issues add their pages to the menu."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(step_id="init", menu_options=["storm"])

    async def async_step_storm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**DEFAULT_OPTIONS, **self.config_entry.options}
        if user_input is not None:
            return self.async_create_entry(data={**current, **user_input})
        schema = {vol.Required(OPT_STORM_LIMIT): _number(10, 200, 1, "km/h")}
        return self.async_show_form(step_id="storm", data_schema=_with_defaults(schema, current))


SHUTTER = {
    vol.Required(CONF_COVER): selector.EntitySelector(selector.EntitySelectorConfig(domain="cover")),
    vol.Optional(CONF_NAME): str,
    vol.Required(CONF_AZIMUTH): _number(0, 359, 1, "°"),
    vol.Required(CONF_TILT): _number(0, 90, 1, "°"),
    vol.Required(CONF_MIN_ELEVATION): _number(0, 90, 1, "°"),
    vol.Required(CONF_MAX_ELEVATION): _number(0, 90, 1, "°"),
    vol.Optional(CONF_ROOM_TEMPERATURE): _sensor("temperature"),
    vol.Required(CONF_MAX_POSITION): _number(0, 100, 5, "%"),
}


class ShutterSubentryFlow(ConfigSubentryFlow):
    """Add or change one shutter."""

    def _errors(self, user_input: dict[str, Any], subentry_id: str | None = None) -> dict[str, str]:
        errors: dict[str, str] = {}
        state = self.hass.states.get(user_input[CONF_COVER])
        features = int(state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)) if state else 0
        if state is not None and not features & CoverEntityFeature.SET_POSITION:
            errors[CONF_COVER] = "no_position"
        for sub in self._get_entry().subentries.values():
            if sub.subentry_id != subentry_id and sub.data.get(CONF_COVER) == user_input[CONF_COVER]:
                errors[CONF_COVER] = "already_configured"
        if user_input[CONF_MIN_ELEVATION] >= user_input[CONF_MAX_ELEVATION]:
            errors[CONF_MAX_ELEVATION] = "elevation_order"
        return errors

    def _title(self, user_input: dict[str, Any]) -> str:
        if user_input.get(CONF_NAME):
            return user_input[CONF_NAME]
        state = self.hass.states.get(user_input[CONF_COVER])
        return state.name if state else user_input[CONF_COVER]

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = self._errors(user_input)
            if not errors:
                return self.async_create_entry(
                    title=self._title(user_input), data=user_input, unique_id=user_input[CONF_COVER]
                )
        values = {**DEFAULT_SHUTTER, **(user_input or {})}
        return self.async_show_form(
            step_id="user", data_schema=_with_defaults(SHUTTER, values), errors=errors
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        subentry = self._get_reconfigure_subentry()
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = self._errors(user_input, subentry.subentry_id)
            if not errors:
                return self.async_update_and_abort(
                    self._get_entry(),
                    subentry,
                    title=self._title(user_input),
                    data=user_input,
                    unique_id=user_input[CONF_COVER],
                )
        values = {**DEFAULT_SHUTTER, **dict(subentry.data), **(user_input or {})}
        return self.async_show_form(
            step_id="reconfigure", data_schema=_with_defaults(SHUTTER, values), errors=errors
        )
