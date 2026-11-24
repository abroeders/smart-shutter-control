"""Config flow of the base controller; the options and subentry flows are in their own modules."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from .const import (
    CONF_LIGHT,
    CONF_LUX_LIMIT,
    CONF_PV_POWER,
    CONF_SUN_SOURCE,
    DEFAULT_LUX_LIMIT,
    DEFAULT_NAME,
    DEFAULT_OPTIONS,
    DOMAIN,
    SUBENTRY_SHUTTER,
)
from .flow_common import (
    SOURCES,
    SUN_FIELDS,
    _with_defaults,
)
from .options_flow import SmartShutterControlOptionsFlow
from .recorder_stats import lux_maxima
from .subentry_flow import ShutterSubentryFlow


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

    _sources: dict[str, Any] | None = None
    _reconfiguring = False
    _warned: tuple[str, ...] | None = None

    async def async_step_sources(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return await self._next_sun_step(user_input)
        return self.async_show_form(step_id="sources", data_schema=vol.Schema(SOURCES))

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            self._reconfiguring = True
            return await self._next_sun_step(user_input)
        current = {CONF_SUN_SOURCE: "pv" if entry.data.get(CONF_PV_POWER) else "none", **entry.data}
        return self.async_show_form(step_id="reconfigure", data_schema=_with_defaults(SOURCES, current))

    async def _next_sun_step(self, sources: dict[str, Any]) -> ConfigFlowResult:
        self._sources = sources
        source = sources[CONF_SUN_SOURCE]
        if source == "pv":
            return await self.async_step_pv()
        if source == "light":
            return await self.async_step_light()
        return self._finish({})

    def _finish(self, sun_fields: dict[str, Any]) -> ConfigFlowResult:
        data = {**(self._sources or {}), **sun_fields}  # the other source's fields are left out
        if self._reconfiguring:
            return self.async_update_reload_and_abort(self._get_reconfigure_entry(), data=data)
        return self.async_create_entry(title=self._name, data=data, options=dict(DEFAULT_OPTIONS))

    def _current(self) -> dict[str, Any]:
        return dict(self._get_reconfigure_entry().data) if self._reconfiguring else {}

    async def async_step_pv(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self._finish(user_input)
        return self.async_show_form(
            step_id="pv", data_schema=_with_defaults(SUN_FIELDS["pv"], self._current())
        )

    async def async_step_light(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = self._current()
        errors: dict[str, str] = {}
        if user_input is not None:
            sensors = tuple(sorted(user_input[CONF_LIGHT]))
            maxima, saturates = await lux_maxima(self.hass, list(sensors))
            # a sensor that probably saturates: say so once; submitting again saves anyway
            if not saturates or self._warned == sensors:
                return self._finish(user_input)
            self._warned, current, errors = sensors, user_input, {"base": "saturates"}
        else:
            maxima, _ = await lux_maxima(self.hass, list(current.get(CONF_LIGHT) or []))
        return self.async_show_form(
            step_id="light",
            data_schema=_with_defaults(SUN_FIELDS["light"], {CONF_LUX_LIMIT: DEFAULT_LUX_LIMIT, **current}),
            description_placeholders={"maxima": maxima},
            errors=errors,
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
