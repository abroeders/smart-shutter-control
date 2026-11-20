"""Automatic control on/off per shutter."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import ShutterEntity, add_per_shutter


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    add_per_shutter(
        entry.runtime_data,
        async_add_entities,
        lambda c, s: [AutomaticSwitch(c, s, "automatic"), HeatProtectionSwitch(c, s, "heat_protection")],
    )


class AutomaticSwitch(ShutterEntity, SwitchEntity):
    """Off: only manual operation; the controller never moves this shutter."""

    @property
    def is_on(self) -> bool:
        return self.controller.automatic

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.controller.set_automatic(True)
        await self.coordinator.async_tick()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.controller.set_automatic(False)
        await self.coordinator.async_tick()


class HeatProtectionSwitch(ShutterEntity, SwitchEntity):
    """Heat protection (sun on the window) for this shutter."""

    @property
    def is_on(self) -> bool:
        return self.controller.heat_protection

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.controller.set_heat_protection(True)
        await self.coordinator.async_tick()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.controller.set_heat_protection(False)
        await self.coordinator.async_tick()
