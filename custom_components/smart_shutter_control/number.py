"""Maximum position per shutter: automatic control never goes above it."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import ShutterEntity, add_per_shutter


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    add_per_shutter(
        entry.runtime_data,
        async_add_entities,
        lambda c, s: [
            OpeningNumber(c, s, "opening"),
            MaxPositionNumber(c, s, "max_position"),
            ShadingPositionNumber(c, s, "shading_position"),
            GlarePositionNumber(c, s, "glare_position"),
            GlareFromNumber(c, s, "glare_from"),
        ],
    )


class MaxPositionNumber(ShutterEntity, NumberEntity):
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def native_value(self) -> float:
        return self.controller.max_position

    async def async_set_native_value(self, value: float) -> None:
        self.controller.set_max_position(int(value))
        await self.coordinator.async_tick()


class ShadingPositionNumber(MaxPositionNumber):
    """Position while the sun shines on the window (heat protection)."""

    @property
    def native_value(self) -> float:
        return self.controller.shading_position

    async def async_set_native_value(self, value: float) -> None:
        self.controller.set_shading_position(int(value))
        await self.coordinator.async_tick()


class GlarePositionNumber(MaxPositionNumber):
    """Position while bright sun shines on the window (glare protection, #36)."""

    @property
    def native_value(self) -> float:
        return self.controller.glare_position

    async def async_set_native_value(self, value: float) -> None:
        self.controller.set_glare_position(int(value))
        await self.coordinator.async_tick()


class GlareFromNumber(MaxPositionNumber):
    """Sun factor (% of the clear-sky value) from which the sun dazzles."""

    _attr_native_min_value = 10

    @property
    def native_value(self) -> float:
        return self.controller.glare_from

    async def async_set_native_value(self, value: float) -> None:
        self.controller.set_glare_from(int(value))
        await self.coordinator.async_tick()


class OpeningNumber(ShutterEntity, NumberEntity):
    """The real opening of the window in %: shows the calibrated position, and moves the shutter there.

    Like operating the shutter by hand: no maximum position applies.
    """

    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.BOX

    @property
    def available(self) -> bool:
        return self.controller.position() is not None

    @property
    def native_value(self) -> float | None:
        return self.controller.position()

    async def async_set_native_value(self, value: float) -> None:
        await self.controller.async_manual(int(round(value)))
