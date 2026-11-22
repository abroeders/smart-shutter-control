"""Temperatures and wind speeds in any unit count as °C and km/h (#64)."""

import pytest
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.smart_shutter_control.const import DEFAULT_OPTIONS, DOMAIN
from custom_components.smart_shutter_control.units import to_celsius, to_kmh

from .conftest import LIVING, OUTDOOR, add_shutter

GUST = "sensor.gust"
ROOM = "sensor.room"
WEATHER = "weather.home"


@pytest.mark.parametrize(
    ("value", "unit", "celsius"),
    [(77, "°F", 25), (298.15, "K", 25), (25, "°C", 25), (25, None, 25), (25, "bogus", 25)],
)
def test_to_celsius(value, unit, celsius) -> None:
    assert to_celsius(value, unit) == pytest.approx(celsius)


@pytest.mark.parametrize(
    ("value", "unit", "kmh"),
    [(31.0686, "mph", 50), (10, "m/s", 36), (10, "kn", 18.52), (50, "km/h", 50), (50, None, 50)],
)
def test_to_kmh(value, unit, kmh) -> None:
    assert to_kmh(value, unit) == pytest.approx(kmh, rel=1e-4)


def temperature(hass: HomeAssistant, entity_id: str, value: float, unit: str) -> None:
    hass.states.async_set(entity_id, str(value), {"device_class": "temperature", "unit_of_measurement": unit})


async def setup(hass: HomeAssistant, **data) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="House",
        data={"outdoor_temperature": OUTDOOR, **data},
        options={**DEFAULT_OPTIONS, "storm_gust_limit": 70},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_outdoor_in_fahrenheit_below_freezing_is_frost(hass: HomeAssistant, covers) -> None:
    temperature(hass, OUTDOOR, 28, "°F")  # -2.2 °C
    entry = await setup(hass)
    await entry.runtime_data.async_tick()
    assert entry.runtime_data.inputs.outdoor == pytest.approx(-2.22, abs=0.01)
    assert entry.runtime_data.frost.active

    temperature(hass, OUTDOOR, 50, "°F")  # 10 °C, a mild day, not 50 °C
    await entry.runtime_data.async_tick()
    assert entry.runtime_data.inputs.outdoor == pytest.approx(10)


async def test_gust_in_mph_is_a_storm(hass: HomeAssistant, covers) -> None:
    temperature(hass, OUTDOOR, 10, "°C")
    hass.states.async_set(GUST, "50", {"device_class": "wind_speed", "unit_of_measurement": "mph"})
    entry = await setup(hass, wind_gust=GUST)
    await entry.runtime_data.async_tick()
    assert entry.runtime_data.inputs.gust == pytest.approx(80.47, abs=0.01)
    assert entry.runtime_data.storm.active  # 80 km/h above 70; read as km/h it would not be

    hass.states.async_set(GUST, "50", {"device_class": "wind_speed", "unit_of_measurement": "km/h"})
    await entry.runtime_data.async_tick()
    assert entry.runtime_data.inputs.gust == 50


async def test_room_temperature_in_fahrenheit(hass: HomeAssistant, covers) -> None:
    temperature(hass, OUTDOOR, 10, "°C")
    temperature(hass, ROOM, 77, "°F")
    entry = await setup(hass)
    await add_shutter(hass, entry, LIVING, room_temperature=ROOM)
    controller = next(iter(entry.runtime_data.shutters.values()))
    assert controller.room_temperature() == pytest.approx(25)


async def test_forecast_in_fahrenheit(hass: HomeAssistant, covers) -> None:
    temperature(hass, OUTDOOR, 10, "°C")
    hass.states.async_set(WEATHER, "sunny", {"temperature_unit": "°F"})

    async def get_forecasts(call: ServiceCall) -> dict:
        today = dt_util.now().date().isoformat()
        return {call.data["entity_id"]: {"forecast": [{"datetime": f"{today}T12:00:00", "temperature": 86}]}}

    hass.services.async_register(
        "weather", "get_forecasts", get_forecasts, supports_response=SupportsResponse.ONLY
    )
    entry = await setup(hass, weather=WEATHER)
    await entry.runtime_data.async_refresh_forecast()
    assert entry.runtime_data.forecast_max == pytest.approx(30)  # 86 °F
    assert entry.runtime_data.hot_day  # 30 °C reaches 28 °C
