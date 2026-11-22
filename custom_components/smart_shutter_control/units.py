"""Temperatures to °C and wind speeds to km/h, whatever unit a sensor reports in (#64).

The rules in core/ work in °C and km/h. A value without a unit, or with one the converter does not know,
counts as °C or km/h.
"""

from __future__ import annotations

from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import State
from homeassistant.util.unit_conversion import BaseUnitConverter, SpeedConverter, TemperatureConverter


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
    value = _value(state)
    return None if value is None else to_celsius(value, state.attributes.get(ATTR_UNIT_OF_MEASUREMENT))


def speed(state: State | None) -> float | None:
    """A wind sensor's state in km/h."""
    value = _value(state)
    return None if value is None else to_kmh(value, state.attributes.get(ATTR_UNIT_OF_MEASUREMENT))
