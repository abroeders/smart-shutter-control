"""Sunny (base controller) and sun on the window (per shutter)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import BaseEntity, ShutterEntity, add_per_shutter


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities(
        [
            SunnySensor(entry.runtime_data, "sunny"),
            FreeDaySensor(entry.runtime_data, "holiday"),
            StormSensor(entry.runtime_data, "storm"),
            FrostSensor(entry.runtime_data, "frost"),
            WinterSensor(entry.runtime_data, "winter"),
        ]
    )
    add_per_shutter(
        entry.runtime_data,
        async_add_entities,
        lambda c, s: [SunOnWindowSensor(c, s, "sun_on_window"), ManualPauseSensor(c, s, "manual_pause")],
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


class FreeDaySensor(BaseEntity, BinarySensorEntity):
    """Today is a weekend day or a holiday: the schedules use their weekend times."""

    @property
    def is_on(self) -> bool:
        return self.coordinator.calendar.is_free(dt_util.now().date())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"holiday": self.coordinator.calendar.holiday(dt_util.now().date())}


class ManualPauseSensor(ShutterEntity, BinarySensorEntity):
    """Automatic control is paused after a manual action."""

    @property
    def is_on(self) -> bool:
        return self.controller.pause.on

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.controller.pause_info()


def _iso(epoch: float | None) -> str | None:
    return None if epoch is None else dt_util.utc_from_timestamp(epoch).isoformat()


class StormSensor(BaseEntity, BinarySensorEntity):
    """Storm: shutters with automatic control are only fully open or fully closed."""

    @property
    def is_on(self) -> bool:
        return self.coordinator.storm.active

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        s = self.coordinator.storm
        return {"source": s.source, "value": s.value, "since": _iso(s.since), "until": _iso(s.until)}


class FrostSensor(BaseEntity, BinarySensorEntity):
    """Frost: the controller does not move the shutters."""

    @property
    def is_on(self) -> bool:
        return self.coordinator.frost.active

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"since": _iso(self.coordinator.frost.since)}


class WinterSensor(BaseEntity, BinarySensorEntity):
    """Winter mode is active (auto: the 24-hour mean outdoor temperature is below the limit)."""

    @property
    def is_on(self) -> bool:
        return self.coordinator.winter.active

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        mean = self.coordinator.outdoor_mean.mean(self.coordinator.inputs.now)
        return {"mean_24h": None if mean is None else round(mean, 1), "mode": self.coordinator.winter.mode}
