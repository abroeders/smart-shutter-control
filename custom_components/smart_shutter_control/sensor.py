"""Why a shutter is where it is, and when it will move next."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .core.model import Reason
from .entity import BaseEntity, ShutterEntity, add_per_shutter


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([SunFactorSensor(entry.runtime_data, "sun_factor")])
    add_per_shutter(
        entry.runtime_data,
        async_add_entities,
        lambda c, s: [
            ReasonSensor(c, s, "reason"),
            NextActionSensor(c, s, "next_action"),
            CalibrationSensor(c, s, "calibration"),
            StandSensor(c, s, "stand"),
            PhaseSensor(c, s, "phase"),
        ],
    )


class ReasonSensor(ShutterEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [r.value for r in Reason]

    @property
    def native_value(self) -> str:
        return str(self.controller.decision.reason)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "target_position": self.controller.decision.position,
            "max_position": self.controller.max_position,
            "language": self.coordinator.language,
        }


class NextActionSensor(ShutterEntity, SensorEntity):
    """When the schedule moves the shutter next, and to what."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> datetime | None:
        change = self.controller.next_change()
        return None if change is None else change.at

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        change = self.controller.next_change()
        if change is None:
            return {}
        following = self.controller.next_changes(3)[1:]
        return {
            "phase": change.phase.value,
            "position": self.controller.target_of(change.phase),
            "following": [
                {
                    "at": t.at.isoformat(),
                    "phase": t.phase.value,
                    "position": self.controller.target_of(t.phase),
                }
                for t in following
            ],
            "overrides": self.controller.overrides(),
        }


class CalibrationSensor(ShutterEntity, SensorEntity):
    """Whether the shutter is calibrated, with the model per direction."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["calibrated", "not_calibrated"]
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str:
        return "calibrated" if self.controller.calibration.calibrated else "not_calibrated"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        calibration = self.controller.calibration
        summary = calibration.summary() if hasattr(calibration, "summary") else {}
        return {"directions": summary, "points": self.controller.calibration_points()}


class SunFactorSensor(BaseEntity, SensorEntity):
    """PV power as a share of the clear-sky power for this position of the sun."""

    _attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> float | None:
        factor = self.coordinator.sunny.factor
        return None if factor is None else round(factor * 100)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        sun = self.coordinator.inputs.sun
        return {
            "source": self.coordinator.sunny.source,
            "sun_source": self.coordinator.sun_source,
            "weather": self.coordinator.weather_state,  # for the view through the window in the card (#30)
            "lux": self.coordinator.sunny.value if self.coordinator.sun_source == "light" else None,
            "sun_azimuth": None if sun is None else round(sun.azimuth, 1),
            "sun_elevation": None if sun is None else round(sun.elevation, 1),
        }


class StandSensor(ShutterEntity, SensorEntity):
    """Closed, slit (gaps open, bottom bar on the sill), partly open or open."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["closed", "slit", "partly_open", "open"]

    @property
    def native_value(self) -> str | None:
        module = self.controller.adapter.module_position()
        position = self.controller.position()
        if module is None or position is None:
            return None
        if module == 0:
            return "closed"
        if position == 0:
            return "slit"
        return "open" if position >= 100 else "partly_open"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "opening": self.controller.position(),
            "module_position": self.controller.adapter.module_position(),
        }


class PhaseSensor(ShutterEntity, SensorEntity):
    """The phase of the shutter's day: night, slit, day or dusk."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["night", "slit", "day", "dusk"]

    @property
    def native_value(self) -> str:
        return self.controller.phase().value
