"""Repository for the runtime state of the shutters: what survives a restart."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORE_VERSION

SAVE_DELAY = 5.0  # s


class RuntimeStore:
    """Per shutter (subentry id): automatic on/off, maximum position, last command."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(hass, STORE_VERSION, f"{DOMAIN}.{entry_id}")
        self.data: dict[str, dict[str, Any]] = {}

    async def async_load(self) -> None:
        self.data = (await self._store.async_load() or {}).get("shutters", {})

    def get(self, shutter_id: str, key: str, default: Any = None) -> Any:
        return self.data.get(shutter_id, {}).get(key, default)

    def set(self, shutter_id: str, key: str, value: Any) -> None:
        self.data.setdefault(shutter_id, {})[key] = value
        self._store.async_delay_save(lambda: {"shutters": self.data}, SAVE_DELAY)

    def forget(self, keep: set[str]) -> None:
        """Drop the state of shutters that no longer exist."""
        for shutter_id in set(self.data) - keep:
            del self.data[shutter_id]

    async def async_remove(self) -> None:
        await self._store.async_remove()
