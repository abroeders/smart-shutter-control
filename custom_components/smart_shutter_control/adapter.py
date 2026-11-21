"""The only place that moves a physical shutter (adapter)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.cover import ATTR_CURRENT_POSITION, ATTR_POSITION, CoverEntityFeature
from homeassistant.components.cover import DOMAIN as COVER_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_SET_COVER_POSITION,
    SERVICE_STOP_COVER,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)


IDLE_W = 5.0  # W: a stopped motor uses less than this
# the ends go by the module's own open/close (its arrows): it runs until it stops at its limit, where a
# position stops on the module's travel-time estimate, short of the limit when that estimate drifts
ENDS = {
    100: (SERVICE_OPEN_COVER, CoverEntityFeature.OPEN),
    0: (SERVICE_CLOSE_COVER, CoverEntityFeature.CLOSE),
}


@dataclass(frozen=True)
class Command:
    position: int  # module position that was sent
    at: float  # epoch seconds
    automatic: bool  # sent by the controller (True) or for a user through our cover entity (False)


class CoverAdapter:
    """Sends positions to the physical cover and remembers what it sent (for manual detection, #5)."""

    def __init__(self, hass: HomeAssistant, entity_id: str, power_entity: str | None = None) -> None:
        self.hass = hass
        self.entity_id = entity_id
        self.last_command: Command | None = None
        self.power_entity = power_entity or self._find_power_sensor()
        # called before each command: (module position, position before, automatic) — for #5
        self.on_send: Callable[[int, int | None, bool], None] | None = None

    def _find_power_sensor(self) -> str | None:
        """A power sensor on the same device as the cover (shutter modules usually measure the motor)."""
        from homeassistant.helpers import entity_registry as er

        registry = er.async_get(self.hass)
        cover = registry.async_get(self.entity_id)
        if cover is None or cover.device_id is None:
            return None
        candidates = []
        for entry in er.async_entries_for_device(registry, cover.device_id):
            if entry.domain == "sensor" and not entry.disabled_by:
                device_class = entry.device_class or entry.original_device_class
                if device_class == "power" or entry.unit_of_measurement == "W":
                    candidates.append(entry.entity_id)

        def idle_first(entity_id: str) -> tuple[int, str]:
            """A motor standing still uses (almost) nothing: a sensor that shows more is not the motor's."""
            state = self.hass.states.get(entity_id)
            try:
                return (0 if state and float(state.state) <= IDLE_W else 1, entity_id)
            except ValueError:
                return (2, entity_id)

        return min(candidates, key=idle_first) if candidates else None

    def reported_since(self, moment: datetime) -> bool:
        """Whether the cover reported (a change or the same position) after this moment."""
        state = self.hass.states.get(self.entity_id)
        if state is None:
            return False
        reported = getattr(state, "last_reported", None) or state.last_updated
        return reported > moment

    async def async_refresh(self) -> None:
        """Ask the integration of the cover to read its position now (Z-Wave: a poll)."""
        try:
            await self.hass.services.async_call(
                "homeassistant", "update_entity", {ATTR_ENTITY_ID: self.entity_id}, blocking=True
            )
        except (HomeAssistantError, ValueError) as err:
            _LOGGER.debug("Could not refresh %s: %s", self.entity_id, err)

    def motor_power(self) -> float | None:
        """Motor power in W, or None without a (working) power sensor."""
        state = self.hass.states.get(self.power_entity) if self.power_entity else None
        try:
            return float(state.state) if state else None
        except ValueError:
            return None

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
        if self.on_send is not None:
            self.on_send(position, self.module_position(), automatic)
        service, data = SERVICE_SET_COVER_POSITION, {ATTR_ENTITY_ID: self.entity_id, ATTR_POSITION: position}
        end = ENDS.get(position)
        if end is not None and self.supported_features() & end[1]:
            service, data = end[0], {ATTR_ENTITY_ID: self.entity_id}
        try:
            await self.hass.services.async_call(COVER_DOMAIN, service, data, blocking=True)
        except HomeAssistantError as err:
            _LOGGER.warning("Could not move %s to %s: %s", self.entity_id, position, err)
            return False
        self.last_command = Command(position, time.time(), automatic)
        return True

    async def async_stop(self) -> None:
        await self.hass.services.async_call(
            COVER_DOMAIN, SERVICE_STOP_COVER, {ATTR_ENTITY_ID: self.entity_id}, blocking=True
        )
