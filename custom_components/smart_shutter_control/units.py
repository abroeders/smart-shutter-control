"""Temperatures to °C and wind speeds to km/h, whatever unit a sensor reports in (#64).

The rules in core/ work in °C and km/h. A value without a unit, or with one the converter does not know,
counts as °C or km/h. `DisplayUnit` shows the settings in the user's unit system (#65), lengths too (#71).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.util.unit_conversion import (
    BaseUnitConverter,
    DistanceConverter,
    SpeedConverter,
    TemperatureConverter,
)
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM


def _convert(converter: type[BaseUnitConverter], value: float, unit: str | None, to: str) -> float:
    if not unit or unit == to or unit not in converter.VALID_UNITS:
        return value
    return converter.convert(value, unit, to)


def to_celsius(value: float, unit: str | None) -> float:
    return _convert(TemperatureConverter, value, unit, UnitOfTemperature.CELSIUS)


def to_kmh(value: float, unit: str | None) -> float:
    return _convert(SpeedConverter, value, unit, UnitOfSpeed.KILOMETERS_PER_HOUR)


def _value(state: State | None) -> float | None:
    if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
        return None
    try:
        return float(state.state)
    except ValueError:
        return None


def temperature(state: State | None) -> float | None:
    """A temperature sensor's state in °C."""
    if state is None:
        return None
    value = _value(state)
    return None if value is None else to_celsius(value, state.attributes.get(ATTR_UNIT_OF_MEASUREMENT))


def speed(state: State | None) -> float | None:
    """A wind sensor's state in km/h."""
    if state is None:
        return None
    value = _value(state)
    return None if value is None else to_kmh(value, state.attributes.get(ATTR_UNIT_OF_MEASUREMENT))


@dataclass(frozen=True)
class DisplayUnit:
    """A setting stored in °C, km/h, cm or m, shown and entered in the user's unit (#65, #71)."""

    converter: type[BaseUnitConverter]
    stored_unit: str
    unit: str
    step: float = 1  # of the shown value
    digits: int = 1  # of a changed value when it is stored

    @property
    def converts(self) -> bool:
        return self.unit != self.stored_unit

    def _to_shown(self, value: float) -> float:
        return self.converter.convert(value, self.stored_unit, self.unit)

    def _to_step(self, value: float) -> float:
        return round(value / self.step) * self.step

    def selector_config(self, low: float, high: float, step: float) -> dict:
        """A number selector's range and step in the shown unit, the range rounded outwards to the step."""
        if not self.converts:
            return {"min": low, "max": high, "step": step, "unit_of_measurement": self.unit}
        return {
            "min": math.floor(self._to_shown(low) / self.step) * self.step,
            "max": math.ceil(self._to_shown(high) / self.step) * self.step,
            "step": self.step,
            "unit_of_measurement": self.unit,
        }

    def shown(self, stored: float | None) -> float | None:
        if stored is None or not self.converts:
            return stored
        return float(self._to_step(self._to_shown(stored)))

    def to_stored(self, shown: float) -> float:
        """A shown value in the stored unit, not rounded."""
        return self.converter.convert(shown, self.unit, self.stored_unit) if self.converts else shown

    def stored(self, shown: float | None, previous: float | None = None) -> float | None:
        """The value to store; a value the user left unchanged keeps its stored value exactly."""
        if shown is None or not self.converts:
            return shown
        if previous is not None and self.shown(previous) == shown:
            return previous
        return round(self.to_stored(shown), self.digits)


def temperature_unit(hass: HomeAssistant) -> DisplayUnit:
    return DisplayUnit(TemperatureConverter, UnitOfTemperature.CELSIUS, hass.config.units.temperature_unit)


def speed_unit(hass: HomeAssistant) -> DisplayUnit:
    """mph with US customary units, otherwise km/h (the metric system's wind unit is m/s)."""
    unit = (
        UnitOfSpeed.MILES_PER_HOUR
        if hass.config.units is US_CUSTOMARY_SYSTEM
        else UnitOfSpeed.KILOMETERS_PER_HOUR
    )
    return DisplayUnit(SpeedConverter, UnitOfSpeed.KILOMETERS_PER_HOUR, unit)


def length_unit(hass: HomeAssistant, stored_unit: str, step: float = 1) -> DisplayUnit:
    """Inches for cm and feet for m with US customary units, otherwise the stored unit (#71)."""
    us = hass.config.units is US_CUSTOMARY_SYSTEM
    if stored_unit == UnitOfLength.METERS:
        unit, digits = (UnitOfLength.FEET if us else stored_unit), 2
    else:
        unit, digits = (UnitOfLength.INCHES if us else stored_unit), 1
    return DisplayUnit(DistanceConverter, stored_unit, unit, step, digits)
