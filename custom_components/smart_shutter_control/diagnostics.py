"""Diagnostics: one JSON file with the settings and the state of the base controller and every shutter."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration
from homeassistant.util.unit_system import METRIC_SYSTEM

from .const import DOMAIN

REDACTED = "**REDACTED**"
TO_REDACT = {"latitude", "longitude", "elevation", "location_name", "home_zone", "location", "address"}
PRIVATE_PREFIXES = ("person.", "device_tracker.")


def _redact_entities(value: Any) -> Any:
    """Replace person and device tracker entity IDs wherever they appear."""
    if isinstance(value, str):
        return REDACTED if value.startswith(PRIVATE_PREFIXES) else value
    if isinstance(value, dict):
        return {key: _redact_entities(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact_entities(item) for item in value]
    return value


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    coordinator = entry.runtime_data
    integration = await async_get_integration(hass, DOMAIN)
    result = {
        "integration": {
            "version": str(integration.version),
            "home_assistant": HA_VERSION,
            "unit_system": "metric" if hass.config.units is METRIC_SYSTEM else "us_customary",
            "time_zone": hass.config.time_zone,
        },
        "entry": {"data": dict(entry.data), "options": dict(entry.options)},
        "base": coordinator.diagnostics(),
        "shutters": [controller.diagnostics() for controller in coordinator.shutters.values()],
    }
    return _redact_entities(async_redact_data(result, TO_REDACT))
