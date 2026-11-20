"""Sunny (base controller) and sun on the window (per shutter)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import BaseEntity, ShutterEntity, add_per_shutter


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([SunnySensor(entry.runtime_data, "sunny")])
    add_per_shutter(
        entry.runtime_data, async_add_entities, lambda c, s: [SunOnWindowSensor(c, s, "sun_on_window")]
    )


class SunnySensor(BaseEntity, BinarySensorEntity):
    @property
    def is_on(self) -> bool:
        return self.coordinator.sunny.sunny


class SunOnWindowSensor(ShutterEntity, BinarySensorEntity):
    """Geometry only: the sun is in front of the window and not blocked."""

    @property
    def is_on(self) -> bool:
        return self.controller.heat_rule.sun_on

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        incidence = self.controller.heat_rule.incidence
        return {
            "incidence": None if incidence is None else round(incidence, 1),
            "phase": str(self.controller.heat_rule.phase),
        }
