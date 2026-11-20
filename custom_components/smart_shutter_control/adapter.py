"""The only place that moves a physical shutter (adapter)."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from homeassistant.components.cover import ATTR_CURRENT_POSITION, ATTR_POSITION
from homeassistant.components.cover import DOMAIN as COVER_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_SET_COVER_POSITION,
    SERVICE_STOP_COVER,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Command:
    position: int  # module position that was sent
    at: float  # epoch seconds
    automatic: bool  # sent by the controller (True) or for a user through our cover entity (False)


class CoverAdapter:
    """Sends positions to the physical cover and remembers what it sent (for manual detection, #5)."""

    def __init__(self, hass: HomeAssistant, entity_id: str) -> None:
        self.hass = hass
        self.entity_id = entity_id
        self.last_command: Command | None = None

    def module_position(self) -> int | None:
        state = self.hass.states.get(self.entity_id)
        if state is None or state.state == STATE_UNAVAILABLE:
            return None
        value = state.attributes.get(ATTR_CURRENT_POSITION)
        return None if value is None else int(value)

    def supported_features(self) -> int:
        state = self.hass.states.get(self.entity_id)
        return int(state.attributes.get("supported_features", 0)) if state else 0

    async def async_move(self, position: int, automatic: bool = True) -> bool:
        try:
            await self.hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_SET_COVER_POSITION,
                {ATTR_ENTITY_ID: self.entity_id, ATTR_POSITION: position},
                blocking=True,
            )
        except HomeAssistantError as err:
            _LOGGER.warning("Could not move %s to %s: %s", self.entity_id, position, err)
            return False
        self.last_command = Command(position, time.time(), automatic)
        return True

    async def async_stop(self) -> None:
        await self.hass.services.async_call(
            COVER_DOMAIN, SERVICE_STOP_COVER, {ATTR_ENTITY_ID: self.entity_id}, blocking=True
        )
