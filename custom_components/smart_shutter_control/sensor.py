"""Why a shutter is where it is, and when it will move next."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .core.model import Reason
from .entity import ShutterEntity, add_per_shutter


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    add_per_shutter(
        entry.runtime_data,
        async_add_entities,
        lambda c, s: [
            ReasonSensor(c, s, "reason"),
            NextActionSensor(c, s, "next_action"),
            CalibrationSensor(c, s, "calibration"),
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
        }


class NextActionSensor(ShutterEntity, SensorEntity):
    """Filled once there are rules with a schedule (#4); unknown until then."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> datetime | None:
        return None


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
