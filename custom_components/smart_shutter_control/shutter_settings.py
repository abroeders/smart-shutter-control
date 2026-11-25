"""The settings of one shutter (its config subentry), read and typed once (#96)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any

from .const import (
    CONF_AZIMUTH,
    CONF_CALIBRATION,
    CONF_COVER,
    CONF_FACADE_LIGHT,
    CONF_GLARE_FROM,
    CONF_GLARE_POSITION,
    CONF_GLARE_PROTECTION,
    CONF_HEAT_OUTDOOR,
    CONF_HEAT_PROTECTION,
    CONF_HEAT_ROOM,
    CONF_HORIZON,
    CONF_HOT_DAY,
    CONF_LOCKOUT_POSITION,
    CONF_MAX_ELEVATION,
    CONF_MAX_POSITION,
    CONF_MIN_ELEVATION,
    CONF_MOTOR_POWER,
    CONF_OPENED_CONTACT,
    CONF_ROOM_TEMPERATURE,
    CONF_SCHEDULE,
    CONF_SHADING_POSITION,
    CONF_SUN_DEPTH,
    CONF_TILT,
    CONF_TILTED_CONTACT,
    CONF_TRAVEL_TIME,
    CONF_VENTILATION_POSITION,
    CONF_WINDOW_HEIGHT,
    CONF_WINDOW_SILL,
    DEFAULT_SHUTTER,
)
from .core.heat import SunSettings
from .core.horizon import Horizon
from .core.model import ShutterConfig
from .core.shading import RoomGeometry

SUN_OVERRIDES = {CONF_HEAT_OUTDOOR: "heat_outdoor", CONF_HEAT_ROOM: "heat_room", CONF_HOT_DAY: "hot_day"}


@dataclass(frozen=True)
class ShutterSettings:
    """Everything the controller reads from the subentry. The entity settings (maximum position, heat and
    glare protection) are the defaults until a user changes them through their entities."""

    config: ShutterConfig
    max_position: int
    heat_protection: bool
    shading_position: int
    glare_protection: bool
    glare_position: int
    glare_from: int  # % of the clear-sky value
    lockout_position: int
    ventilation_position: int | None = None
    opened_contact: str | None = None
    tilted_contact: str | None = None
    facade_light: str | None = None
    motor_power: str | None = None
    travel_time: float | None = None  # s, fully open to fully closed
    calibration: Mapping[str, Any] | None = None
    schedule_overrides: Mapping[str, Any] = field(default_factory=dict)
    sun_overrides: Mapping[str, float] = field(default_factory=dict)  # SunSettings fields this shutter sets

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> ShutterSettings:
        values = {**DEFAULT_SHUTTER, **data}
        ventilation = values.get(CONF_VENTILATION_POSITION)
        travel = values.get(CONF_TRAVEL_TIME)
        return cls(
            config=shutter_config(values),
            max_position=int(values[CONF_MAX_POSITION]),
            heat_protection=bool(values[CONF_HEAT_PROTECTION]),
            shading_position=int(values[CONF_SHADING_POSITION]),
            glare_protection=bool(values[CONF_GLARE_PROTECTION]),
            glare_position=int(values[CONF_GLARE_POSITION]),
            glare_from=int(values[CONF_GLARE_FROM]),
            lockout_position=int(values[CONF_LOCKOUT_POSITION]),
            ventilation_position=None if ventilation is None else int(ventilation),
            opened_contact=values.get(CONF_OPENED_CONTACT),
            tilted_contact=values.get(CONF_TILTED_CONTACT),
            facade_light=values.get(CONF_FACADE_LIGHT) or None,
            motor_power=values.get(CONF_MOTOR_POWER),
            travel_time=float(travel) if travel else None,
            calibration=values.get(CONF_CALIBRATION),
            schedule_overrides=dict(values.get(CONF_SCHEDULE) or {}),
            sun_overrides={
                name: float(values[key]) for key, name in SUN_OVERRIDES.items() if values.get(key) is not None
            },
        )

    def sun(self, base: SunSettings) -> SunSettings:
        """The base controller's sun settings with this shutter's heat limits and hot day."""
        return replace(base, **self.sun_overrides)

    @property
    def calibration_points(self) -> dict:
        return dict((self.calibration or {}).get("points") or {})


def shutter_config(data: Mapping[str, Any]) -> ShutterConfig:
    values = {**DEFAULT_SHUTTER, **data}
    return ShutterConfig(
        cover=values[CONF_COVER],
        azimuth=float(values[CONF_AZIMUTH]),
        tilt=float(values[CONF_TILT]),
        min_elevation=float(values[CONF_MIN_ELEVATION]),
        max_elevation=float(values[CONF_MAX_ELEVATION]),
        room_temperature=values.get(CONF_ROOM_TEMPERATURE),
        horizon=Horizon.from_data(values.get(CONF_HORIZON)),
        room=room_geometry(values),
    )


def room_geometry(values: Mapping[str, Any]) -> RoomGeometry | None:
    """The room behind the window (#55), when all three are known; the window height may come from the
    calibration."""
    sill, depth = values.get(CONF_WINDOW_SILL), values.get(CONF_SUN_DEPTH)
    height = values.get(CONF_WINDOW_HEIGHT) or (values.get(CONF_CALIBRATION) or {}).get("window_height_cm")
    if sill is None or depth is None or not height:
        return None
    return RoomGeometry(float(sill), float(height), float(depth))
