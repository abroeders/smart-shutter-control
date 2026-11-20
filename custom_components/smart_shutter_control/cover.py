"""The shutter with its calibrated position; commands go to the physical cover."""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import ATTR_POSITION, CoverDeviceClass, CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import ShutterEntity, add_per_shutter

FEATURES = (
    CoverEntityFeature.OPEN
    | CoverEntityFeature.CLOSE
    | CoverEntityFeature.STOP
    | CoverEntityFeature.SET_POSITION
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    add_per_shutter(entry.runtime_data, async_add_entities, lambda c, s: [ShutterCover(c, s, "shutter")])


class ShutterCover(ShutterEntity, CoverEntity):
    _attr_device_class = CoverDeviceClass.SHUTTER

    @property
    def supported_features(self) -> CoverEntityFeature:
        physical = CoverEntityFeature(self.controller.adapter.supported_features())
        return FEATURES & (
            physical | CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.SET_POSITION
        )

    @property
    def available(self) -> bool:
        return self.controller.position() is not None

    @property
    def current_cover_position(self) -> int | None:
        return self.controller.position()

    @property
    def is_closed(self) -> bool | None:
        position = self.controller.position()
        return None if position is None else position == 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        c = self.controller
        return {
            "physical_cover": c.config.cover,
            "module_position": c.adapter.module_position(),
            "direction": str(c.direction()),
            "calibrated": c.calibration.calibrated,
            "slit": c.calibration.slit(c.direction()),
        }

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        await self.controller.async_manual(kwargs[ATTR_POSITION])

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.controller.async_manual(100)

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.controller.async_manual(0)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self.controller.async_stop()
