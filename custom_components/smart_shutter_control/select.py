"""Winter mode for all shutters: auto, on or off (#7); the lock of each shutter (#52)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .core.lock import LockMode
from .entity import BaseEntity, ShutterEntity, add_per_shutter


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([WinterModeSelect(entry.runtime_data, "winter_mode")])
    add_per_shutter(entry.runtime_data, async_add_entities, lambda co, c: [LockSelect(co, c, "lock")])


class WinterModeSelect(BaseEntity, SelectEntity):
    _attr_options = ["auto", "on", "off"]

    @property
    def current_option(self) -> str:
        return self.coordinator.winter.mode

    async def async_select_option(self, option: str) -> None:
        self.coordinator.set_winter_mode(option)
        await self.coordinator.async_tick()


class LockSelect(ShutterEntity, SelectEntity):
    """The shutter's lock (#52): shows it and sets one without a duration."""

    _attr_options = [m.value for m in LockMode]

    @property
    def current_option(self) -> str:
        return self.controller.lock.mode.value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        until = self.controller.lock.until
        return {"until": None if until is None else dt_util.utc_from_timestamp(until).isoformat()}

    async def async_select_option(self, option: str) -> None:
        self.controller.set_lock(option)
        await self.coordinator.async_tick()
