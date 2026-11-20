"""Base class of the entities of one shutter device."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .controller import ShutterController
from .coordinator import BaseCoordinator


class ShutterEntity(CoordinatorEntity[BaseCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: BaseCoordinator, controller: ShutterController, key: str) -> None:
        super().__init__(coordinator)
        self.controller = controller
        entry_id = coordinator.entry.entry_id
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry_id}_{controller.id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, controller.id)},
            name=controller.title,
            manufacturer="Smart Shutter Control",
            model="Shutter controller",
            via_device=(DOMAIN, entry_id),
        )


def add_per_shutter(coordinator: BaseCoordinator, async_add_entities, factory) -> None:
    """Add the entities of each shutter to its own subentry."""
    for controller in coordinator.shutters.values():
        async_add_entities(factory(coordinator, controller), config_subentry_id=controller.id)
