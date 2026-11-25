"""Resume automatic control after a manual action (#5); record the horizon (#54)."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
        lambda c, s: [ResumeButton(c, s, "resume"), SunLeftButton(c, s, "sun_left")],
    )


class ResumeButton(ShutterEntity, ButtonEntity):
    """Ends the manual pause and moves the shutter at once to the position automatic control wants."""

    async def async_press(self) -> None:
        self.controller.resume_all()
        await self.coordinator.async_tick()


class SunLeftButton(ShutterEntity, ButtonEntity):
    """The sun has just left the window: its position now becomes a point of the window's horizon (#54)."""

    async def async_press(self) -> None:
        await self.coordinator.async_record_horizon(self.controller)
