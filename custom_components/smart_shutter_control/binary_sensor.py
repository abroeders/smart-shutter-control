"""Sunny (base controller) and sun on the window (per shutter)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .core.shading import depth_position
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
            HotDaySensor(entry.runtime_data, "hot_day"),
            AwaySensor(entry.runtime_data, "away"),
        ]
    )
    add_per_shutter(
        entry.runtime_data,
        async_add_entities,
        lambda c, s: [
            SunOnWindowSensor(c, s, "sun_on_window"),
            ManualPauseSensor(c, s, "manual_pause"),
            StuckSensor(c, s, "stuck"),
        ],
    )


class SunnySensor(BaseEntity, BinarySensorEntity):
    @property
    def is_on(self) -> bool:
        return self.coordinator.sunny.sunny


class AwaySensor(BaseEntity, BinarySensorEntity):
    """Nobody home for the away delay, or holiday (#51). No device class: `presence` means the opposite."""

    @property
    def is_on(self) -> bool:
        return self.coordinator.away

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        since = self.coordinator.away_state.away_since
        return {"since": None if since is None else dt_util.utc_from_timestamp(since).isoformat()}


class SunOnWindowSensor(ShutterEntity, BinarySensorEntity):
    """Geometry only: the sun is in front of the window and not blocked."""

    @property
    def is_on(self) -> bool:
        return self.controller.rules.heat.sun_on

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        incidence = self.controller.rules.heat.incidence
        attributes = {
            "incidence": None if incidence is None else round(incidence, 1),
            "phase": str(self.controller.rules.heat.phase),
            "glare_phase": str(self.controller.rules.glare.phase),
            # for the view through the window in the card (#30)
            "window_azimuth": self.controller.config.azimuth,
            "window_tilt": self.controller.config.tilt,
        }
        sun = self.coordinator.inputs.sun
        room = self.controller.config.room
        if sun is not None and room is not None and self.controller.config.tilt == 90:  # (#55)
            attributes["shading_from_depth"] = depth_position(room, sun, self.controller.config.azimuth)
        if sun is not None and self.controller.config.horizon.points:  # (#54)
            window = self.controller.window()
            attributes["horizon"] = round(window.lowest_elevation(sun), 1)
        facade = self.controller.facade
        if facade is not None:  # this shutter's own light sensor decides "sunny"
            attributes |= {
                "sunny": facade.sunny,
                "sun_factor": None if facade.factor is None else round(facade.factor * 100),
                "lux": facade.value,
                "source": facade.source,
            }
        return attributes


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


class StuckSensor(ShutterEntity, BinarySensorEntity):
    """The shutter did not reach its target after the command was retried."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool:
        return self.controller.stuck

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "target": self.controller.arrival.target,
            "position": self.controller.adapter.module_position(),
        }


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
        inputs = self.coordinator.inputs
        return {
            "source": s.source,
            "value": s.value,
            "since": _iso(s.since),
            "until": _iso(s.until),
            "wind": inputs.wind,  # km/h, for the trees in the card (#30)
            "gust": inputs.gust,
        }


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


class HotDaySensor(BaseEntity, BinarySensorEntity):
    """Today's forecast maximum reaches the base controller's "hot day from" (#50)."""

    @property
    def is_on(self) -> bool:
        return self.coordinator.hot_day

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        coordinator = self.coordinator
        return {"forecast_max": coordinator.forecast_max, "limit": coordinator.sun_settings().hot_day}
