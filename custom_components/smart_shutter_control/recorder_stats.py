"""Reads of the recorder's long-term statistics for the config and options flows."""

from __future__ import annotations

from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT

from .const import (
    LUX_SATURATES_BELOW,
)
from .units import speed_unit, to_kmh


async def _max_30_days(hass, entity_id: str | None, wind: bool = False) -> str:
    """The highest value of a sensor in the last 30 days (long-term statistics), as text; – when unknown.

    `wind`: from the sensor's unit (#64) in the user's unit, with the unit (#65)."""
    if not entity_id:
        return "–"
    try:
        from datetime import timedelta

        from homeassistant.components.recorder import get_instance
        from homeassistant.components.recorder.statistics import statistics_during_period
        from homeassistant.util import dt as dt_util

        start = dt_util.utcnow() - timedelta(days=30)
        stats = await get_instance(hass).async_add_executor_job(
            statistics_during_period, hass, start, None, {entity_id}, "day", None, {"max"}
        )
        values = [v for row in stats.get(entity_id, []) if (v := row.get("max")) is not None]
        if not values:
            return "–"
        top = max(values)
        if wind:
            state = hass.states.get(entity_id)
            unit = speed_unit(hass)
            shown = unit.shown(to_kmh(top, state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) if state else None))
            return f"{shown:.0f} {unit.unit}"
        return f"{top:.0f}"
    except Exception:  # noqa: BLE001 - no recorder or no statistics: just do not show it
        return "–"


async def lux_maxima(hass, sensors: list[str]) -> tuple[str, bool]:
    """Each light sensor's highest value of the last 30 days, and whether one probably saturates."""
    lines, saturates = [], False
    for entity_id in sensors:
        top = await _max_30_days(hass, entity_id)
        state = hass.states.get(entity_id)
        name = state.name if state else entity_id
        lines.append(f"- {name}: {top} lx")
        if top != "–" and float(top) < LUX_SATURATES_BELOW:
            saturates = True
    return ("\n".join(lines) or "–"), saturates
