"""Automatic control on/off per shutter, and for the whole integration (#53)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import BaseEntity, ShutterEntity, add_per_shutter


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities(
        [
            SleepInAllSwitch(entry.runtime_data, "sleep_in_all"),
            AutomaticAllSwitch(entry.runtime_data, "automatic_all"),
        ]
    )
    add_per_shutter(
        entry.runtime_data,
        async_add_entities,
        lambda c, s: [
            AutomaticSwitch(c, s, "automatic"),
            HeatProtectionSwitch(c, s, "heat_protection"),
            GlareProtectionSwitch(c, s, "glare_protection"),
            SleepInSwitch(c, s, "sleep_in"),
        ],
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


class GlareProtectionSwitch(ShutterEntity, SwitchEntity):
    """Glare protection (bright sun on the window, whatever the temperature) for this shutter (#36)."""

    @property
    def is_on(self) -> bool:
        return self.controller.glare_protection

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.controller.set_glare_protection(True)
        await self.coordinator.async_tick()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.controller.set_glare_protection(False)
        await self.coordinator.async_tick()


class SleepInSwitch(ShutterEntity, SwitchEntity):
    """Keep the shutter closed next morning until it is operated by hand or the sleep-in end time."""

    @property
    def is_on(self) -> bool:
        return self.controller.sleep_in.armed

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.controller.set_sleep_in(True)
        await self.coordinator.async_tick()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.controller.set_sleep_in(False)
        await self.coordinator.async_tick()


class SleepInAllSwitch(BaseEntity, SwitchEntity):
    """Sleep-in for every shutter."""

    @property
    def is_on(self) -> bool:
        return self.coordinator.sleep_in_all

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.coordinator.set_sleep_in_all(True)
        await self.coordinator.async_tick()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.coordinator.set_sleep_in_all(False)
        await self.coordinator.async_tick()


class AutomaticAllSwitch(BaseEntity, SwitchEntity):
    """Off: no shutter moves by itself, not even in a storm (#53); on again: all go where they are wanted."""

    @property
    def is_on(self) -> bool:
        return self.coordinator.automatic_all

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.coordinator.set_automatic_all(True)
        await self.coordinator.async_tick()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.coordinator.set_automatic_all(False)
        await self.coordinator.async_tick()
