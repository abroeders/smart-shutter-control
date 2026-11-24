"""The subentry flow for a shutter."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.cover import CoverEntityFeature
from homeassistant.config_entries import (
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import ATTR_SUPPORTED_FEATURES, CONF_NAME
from homeassistant.helpers import selector

from .calibration_flow import CalibrationSteps
from .const import (
    CONF_AZIMUTH,
    CONF_COVER,
    CONF_FACADE_LIGHT,
    CONF_GLARE_FROM,
    CONF_GLARE_POSITION,
    CONF_GLARE_PROTECTION,
    CONF_HEAT_OUTDOOR,
    CONF_HEAT_PROTECTION,
    CONF_HEAT_ROOM,
    CONF_HORIZON,
    CONF_HOT_DAY,
    CONF_LOCKOUT_POSITION,
    CONF_MAX_ELEVATION,
    CONF_MAX_POSITION,
    CONF_MIN_ELEVATION,
    CONF_MOTOR_POWER,
    CONF_OPENED_CONTACT,
    CONF_ROOM_TEMPERATURE,
    CONF_SCHEDULE,
    CONF_SHADING_POSITION,
    CONF_SUN_DEPTH,
    CONF_SUN_SOURCE,
    CONF_TILT,
    CONF_TILTED_CONTACT,
    CONF_TRAVEL_TIME,
    CONF_VENTILATION_POSITION,
    CONF_WINDOW_HEIGHT,
    CONF_WINDOW_SILL,
    DEFAULT_SHUTTER,
    OPT_SCHEDULE,
)
from .core.horizon import Horizon, from_rows, rows_from
from .core.horizon import check as check_horizon
from .core.schedule import merged
from .flow_common import (
    INHERIT_CHOICES,
    _is_number,
    _number,
    _sensor,
    _shown_form,
    _stored_input,
    _with_defaults,
    base_placeholders,
    schedule_fields,
)
from .units import temperature_unit

SHUTTER = {
    vol.Required(CONF_COVER): selector.EntitySelector(selector.EntitySelectorConfig(domain="cover")),
    vol.Optional(CONF_NAME): str,
    vol.Required(CONF_AZIMUTH): _number(0, 359, 1, "°"),
    vol.Required(CONF_TILT): _number(0, 90, 1, "°"),
    vol.Required(CONF_MIN_ELEVATION): _number(0, 90, 1, "°"),
    vol.Required(CONF_MAX_ELEVATION): _number(0, 90, 1, "°"),
    vol.Optional(CONF_ROOM_TEMPERATURE): _sensor("temperature"),
    vol.Optional(CONF_MOTOR_POWER): _sensor("power"),
    vol.Optional(CONF_TRAVEL_TIME): _number(5, 300, 0.5, "s"),
    vol.Required(CONF_MAX_POSITION): _number(0, 100, 5, "%"),
    vol.Required(CONF_HEAT_PROTECTION): selector.BooleanSelector(),
    vol.Required(CONF_SHADING_POSITION): _number(0, 100, 5, "%"),
    vol.Optional(CONF_WINDOW_SILL): _number(0, 300, 1, "cm"),
    vol.Optional(CONF_WINDOW_HEIGHT): _number(10, 400, 1, "cm"),
    vol.Optional(CONF_SUN_DEPTH): _number(0, 10, 0.1, "m"),
    vol.Optional(CONF_HEAT_OUTDOOR): _number(-10, 40, 0.5, "°C"),
    vol.Optional(CONF_HEAT_ROOM): _number(10, 35, 0.5, "°C"),
    vol.Optional(CONF_HOT_DAY): _number(15, 45, 0.5, "°C"),
    vol.Required(CONF_GLARE_PROTECTION): selector.BooleanSelector(),
    vol.Required(CONF_GLARE_POSITION): _number(0, 100, 5, "%"),
    vol.Required(CONF_GLARE_FROM): _number(10, 100, 5, "%"),
}

_CONTACT = selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor"))
CONTACTS = {  # (#49)
    vol.Optional(CONF_OPENED_CONTACT): _CONTACT,
    vol.Optional(CONF_TILTED_CONTACT): _CONTACT,
    vol.Required(CONF_LOCKOUT_POSITION): _number(0, 100, 5, "%"),
    vol.Optional(CONF_VENTILATION_POSITION): _number(0, 100, 5, "%"),
}


HORIZON_TABLE_LABELS = {
    "en": {"azimuth": "Sun direction (°)", "elevation": "Lowest elevation (°)"},
    "nl": {"azimuth": "Zonrichting (°)", "elevation": "Laagste zonshoogte (°)"},
}


def _without_fields(data: dict[str, Any], schema: dict) -> dict[str, Any]:
    keys = {str(k) for k in schema}
    return {k: v for k, v in data.items() if k not in keys}


class ShutterSubentryFlow(CalibrationSteps, ConfigSubentryFlow):
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

    def _schema(self) -> dict:
        """The shutter's fields; a facade light sensor only when the sun source is light sensors."""
        if self._get_entry().data.get(CONF_SUN_SOURCE) == "light":
            return {**SHUTTER, vol.Optional(CONF_FACADE_LIGHT): _sensor("illuminance")}
        return SHUTTER

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = _stored_input(self.hass, self._schema(), user_input, DEFAULT_SHUTTER)
            errors = self._errors(user_input)
            if not errors:
                return self.async_create_entry(
                    title=self._title(user_input), data=user_input, unique_id=user_input[CONF_COVER]
                )
        values = {**DEFAULT_SHUTTER, **(user_input or {})}
        return self.async_show_form(
            step_id="user", data_schema=_shown_form(self.hass, self._schema(), values), errors=errors
        )

    # --- reconfigure: a menu ------------------------------------------------------------------------
    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return self.async_show_menu(
            step_id="reconfigure",
            menu_options=[
                "settings",
                "schedule",
                "schedule_reset",
                "calibrate",
                "add_point",
                "horizon",
                "contacts",
            ],
        )

    async def async_step_settings(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        subentry = self._get_reconfigure_subentry()
        errors: dict[str, str] = {}
        if user_input is not None:
            previous = {**DEFAULT_SHUTTER, **dict(subentry.data)}
            user_input = _stored_input(self.hass, self._schema(), user_input, previous)
            errors = self._errors(user_input, subentry.subentry_id)
            if not errors:
                return self.async_update_and_abort(
                    self._get_entry(),
                    subentry,
                    title=self._title(user_input),
                    # a cleared optional field must be removed, not kept: replace the form's fields
                    data={**_without_fields(dict(subentry.data), self._schema()), **user_input},
                    unique_id=user_input[CONF_COVER],
                )
        values = {**DEFAULT_SHUTTER, **dict(subentry.data), **(user_input or {})}
        return self.async_show_form(
            step_id="settings", data_schema=_shown_form(self.hass, self._schema(), values), errors=errors
        )

    # --- schedule overrides -----------------------------------------------------------------------
    def _base_schedule(self) -> dict[str, Any]:
        return merged(self._get_entry().options.get(OPT_SCHEDULE), None)

    def _shown_base(self) -> dict[str, Any]:
        """The base schedule with its temperature in the user's unit (#65)."""
        base = self._base_schedule()
        if _is_number(base.get("winter_closed_below")):
            unit = temperature_unit(self.hass)
            base["winter_closed_below"] = f"{unit.shown(base['winter_closed_below']):g} {unit.unit}"
        return base

    async def async_step_schedule(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        subentry = self._get_reconfigure_subentry()
        fields = schedule_fields(base=False)
        if user_input is not None:
            previous = dict(subentry.data.get(CONF_SCHEDULE) or {})
            user_input = _stored_input(self.hass, fields, user_input, previous)
            overrides = {k: v for k, v in user_input.items() if v not in (None, "", "inherit")}
            return self.async_update_and_abort(
                self._get_entry(), subentry, data_updates={CONF_SCHEDULE: overrides}
            )
        overrides = dict(subentry.data.get(CONF_SCHEDULE) or {})
        shown = {**dict.fromkeys(INHERIT_CHOICES, "inherit"), **overrides}
        return self.async_show_form(
            step_id="schedule",
            data_schema=_shown_form(self.hass, fields, shown),
            description_placeholders=base_placeholders(self._shown_base(), self.hass.config.language),
        )

    async def async_step_schedule_reset(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return self.async_update_and_abort(
            self._get_entry(), self._get_reconfigure_subentry(), data_updates={CONF_SCHEDULE: {}}
        )

    # --- horizon table (#54) -------------------------------------------------------------------------
    def _horizon_schema(self) -> dict:
        labels = HORIZON_TABLE_LABELS.get((self.hass.config.language or "en")[:2], HORIZON_TABLE_LABELS["en"])

        def number(low: float, high: float) -> dict:
            return {
                "number": {
                    "min": low,
                    "max": high,
                    "step": 0.1,
                    "mode": "box",
                    "unit_of_measurement": "°",
                }
            }

        rows = selector.ObjectSelector(
            selector.ObjectSelectorConfig(
                multiple=True,
                label_field="azimuth",
                fields={
                    "azimuth": {
                        "label": labels["azimuth"],
                        "required": True,
                        "selector": number(0, 360),
                    },
                    "elevation": {
                        "label": labels["elevation"],
                        "required": True,
                        "selector": number(0, 60),
                    },
                },
            )
        )
        return {vol.Required("rows"): rows}

    async def async_step_horizon(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        subentry = self._get_reconfigure_subentry()
        errors: dict[str, str] = {}
        if user_input is not None:
            rows = [r for r in user_input.get("rows") or [] if isinstance(r, dict)]
            problems = check_horizon(rows)
            if problems:
                errors["base"] = problems[0]
            else:
                return self.async_update_and_abort(
                    self._get_entry(),
                    subentry,
                    data_updates={CONF_HORIZON: from_rows(rows).as_data()},
                )
        stored = Horizon.from_data(subentry.data.get(CONF_HORIZON))
        values = {"rows": rows_from(stored), **(user_input or {})}
        return self.async_show_form(
            step_id="horizon", data_schema=_with_defaults(self._horizon_schema(), values), errors=errors
        )

    async def async_step_contacts(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        subentry = self._get_reconfigure_subentry()
        if user_input is not None:
            return self.async_update_and_abort(
                self._get_entry(),
                subentry,
                data={**_without_fields(dict(subentry.data), CONTACTS), **user_input},
            )
        values = {**DEFAULT_SHUTTER, **dict(subentry.data)}
        return self.async_show_form(step_id="contacts", data_schema=_with_defaults(CONTACTS, values))
