"""Smart Shutter Control: controls roller shutters from Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, PLATFORMS
from .coordinator import BaseCoordinator

type ShutterConfigEntry = ConfigEntry[BaseCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: ShutterConfigEntry) -> bool:
    """Set up the base controller, its device and one device per shutter."""
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Smart Shutter Control",
        model="Base controller",
    )
    coordinator = BaseCoordinator(hass, entry)
    await coordinator.async_start()
    entry.runtime_data = coordinator
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        await coordinator.async_stop()  # no timers left behind when the setup fails
        raise
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    await coordinator.async_tick()
    return True


async def _async_reload(hass: HomeAssistant, entry: ShutterConfigEntry) -> None:
    """Options, sources or shutters changed: start again with the new settings."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ShutterConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_stop()
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: ShutterConfigEntry) -> None:
    from .storage import RuntimeStore

    await RuntimeStore(hass, entry.entry_id).async_remove()
