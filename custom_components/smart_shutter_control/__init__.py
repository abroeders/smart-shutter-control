"""Smart Shutter Control: controls roller shutters from Home Assistant."""

from __future__ import annotations

from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .const import CARD_FILE, CARD_URL, CONF_PV_POWER, CONF_SUN_SOURCE, DOMAIN, PLATFORMS
from .coordinator import BaseCoordinator
from .services import async_register_services

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type ShutterConfigEntry = ConfigEntry[BaseCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the Lovelace card and load it on every dashboard (no manual resource needed); register the
    actions (#52)."""
    async_register_services(hass)
    await async_register_card(hass)
    return True


async def async_register_card(hass: HomeAssistant) -> bool:
    """Register the card's static path and extra module URL; skipped without http or frontend (tests)."""
    if getattr(hass, "http", None) is None or "frontend" not in hass.config.components:
        return False
    from homeassistant.components.frontend import add_extra_js_url
    from homeassistant.components.http import StaticPathConfig

    path = Path(__file__).parent / "frontend" / CARD_FILE
    await hass.http.async_register_static_paths([StaticPathConfig(CARD_URL, str(path), True)])
    version = (await async_get_integration(hass, DOMAIN)).version
    add_extra_js_url(hass, f"{CARD_URL}?v={version}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ShutterConfigEntry) -> bool:
    """Set up the base controller, its device and one device per shutter."""
    if "pv_forecast" in entry.data or CONF_SUN_SOURCE not in entry.data:
        data = {k: v for k, v in entry.data.items() if k != "pv_forecast"}  # pv_forecast: removed in 0.6.1
        data.setdefault(CONF_SUN_SOURCE, "pv" if data.get(CONF_PV_POWER) else "none")
        hass.config_entries.async_update_entry(entry, data=data)
    base = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Smart Shutter Control",
        model="Base controller",
    )
    coordinator = BaseCoordinator(hass, entry)
    coordinator.base_device_id = base.id
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
    if entry.runtime_data.quiet_update():
        return
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ShutterConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_stop()
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: ShutterConfigEntry) -> None:
    from .storage import RuntimeStore

    await RuntimeStore(hass, entry.entry_id).async_remove()
