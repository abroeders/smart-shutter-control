"""Actions of the integration (#52): lock or force shutters from an automation."""

from __future__ import annotations

from datetime import timedelta

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_DEVICE_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .controller import ShutterController
from .coordinator import BaseCoordinator
from .core.lock import LockMode

SERVICE_SET_LOCK = "set_lock"
ATTR_MODE = "mode"
ATTR_DURATION = "duration"

SET_LOCK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(ATTR_MODE): vol.In([m.value for m in LockMode]),
        vol.Optional(ATTR_DURATION): cv.positive_time_period,
    }
)


def async_register_services(hass: HomeAssistant) -> None:
    """Registered once in `async_setup`, as Home Assistant asks; works on every loaded entry."""

    async def set_lock(call: ServiceCall) -> None:
        duration: timedelta | None = call.data.get(ATTR_DURATION)
        found = _controllers(hass, call.data[ATTR_DEVICE_ID])
        for _coordinator, controller in found:
            controller.set_lock(call.data[ATTR_MODE], duration.total_seconds() if duration else None)
        for coordinator in {id(c): c for c, _ in found}.values():
            await coordinator.async_tick()

    hass.services.async_register(DOMAIN, SERVICE_SET_LOCK, set_lock, schema=SET_LOCK_SCHEMA)


def _controllers(
    hass: HomeAssistant, device_ids: list[str]
) -> list[tuple[BaseCoordinator, ShutterController]]:
    """The shutter controllers of the given devices, with their base coordinator; an unknown or non-shutter
    device is an error."""
    shutters: dict[str, tuple[BaseCoordinator, ShutterController]] = {}
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            coordinator: BaseCoordinator = entry.runtime_data
            shutters.update({k: (coordinator, c) for k, c in coordinator.shutters.items()})
    registry = dr.async_get(hass)
    found: list[tuple[BaseCoordinator, ShutterController]] = []
    for device_id in device_ids:
        device = registry.async_get(device_id)
        ids = [value for domain, value in device.identifiers if domain == DOMAIN] if device else []
        controller = next((shutters[i] for i in ids if i in shutters), None)
        if controller is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="not_a_shutter",
                translation_placeholders={"device_id": device_id},
            )
        found.append(controller)
    return found
