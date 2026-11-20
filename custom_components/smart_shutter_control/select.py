"""Winter mode for all shutters: auto, on or off (#7)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import BaseEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([WinterModeSelect(entry.runtime_data, "winter_mode")])


class WinterModeSelect(BaseEntity, SelectEntity):
    _attr_options = ["auto", "on", "off"]

    @property
    def current_option(self) -> str:
        return self.coordinator.winter.mode

    async def async_select_option(self, option: str) -> None:
        self.coordinator.set_winter_mode(option)
        await self.coordinator.async_tick()
