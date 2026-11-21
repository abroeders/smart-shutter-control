"""Repository for the runtime state of the shutters: what survives a restart."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORE_VERSION

SAVE_DELAY = 5.0  # s
GLOBAL_SAVE_DELAY = 300.0  # s: learned data changes every tick; writing it every few minutes is enough


class RuntimeStore:
    """Per shutter (subentry id): automatic on/off, maximum position, last command."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, STORE_VERSION, f"{DOMAIN}.{entry_id}")
        self.data: dict[str, dict[str, Any]] = {}
        self.globals: dict[str, Any] = {}
        self._due: float | None = None  # loop time of the pending save
        self._loaded = False

    async def async_load(self) -> None:
        stored = await self._store.async_load() or {}
        self.data = stored.get("shutters", {})
        self.globals = stored.get("globals", {})
        self._loaded = True

    def _payload(self) -> dict[str, Any]:
        self._due = None
        return {"shutters": self.data, "globals": self.globals}

    def _save_within(self, delay: float) -> None:
        """Save within `delay` seconds; never push a save that is already due sooner further out.

        The learned data changes every tick: without this, its long delay would postpone a changed setting's
        save again and again, and a reload would lose the setting.
        """
        due = self.hass.loop.time() + delay
        if self._due is not None and self._due <= due:
            return
        self._due = due
        self._store.async_delay_save(self._payload, delay)

    def set_global(self, key: str, value: Any, setting: bool = False) -> None:
        """Base controller data such as the learned clear-sky reference; a setting is saved within seconds."""
        self.globals[key] = value
        self._save_within(SAVE_DELAY if setting else GLOBAL_SAVE_DELAY)

    def get(self, shutter_id: str, key: str, default: Any = None) -> Any:
        return self.data.get(shutter_id, {}).get(key, default)

    def set(self, shutter_id: str, key: str, value: Any) -> None:
        self.data.setdefault(shutter_id, {})[key] = value
        self._save_within(SAVE_DELAY)

    async def async_flush(self) -> None:
        """Write now: on unload (a reload, or the integration removed), before the state is gone."""
        if self._loaded:  # never overwrite the stored state with an empty one after a failed start
            await self._store.async_save(self._payload())

    def forget(self, keep: set[str]) -> None:
        """Drop the state of shutters that no longer exist."""
        for shutter_id in set(self.data) - keep:
            del self.data[shutter_id]

    async def async_remove(self) -> None:
        await self._store.async_remove()
