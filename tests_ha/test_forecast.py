"""The weather forecast drives the base hot-day entities and heat protection."""

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.smart_shutter_control.const import DEFAULT_OPTIONS, DOMAIN
from custom_components.smart_shutter_control.core.sun import SunPosition

from .conftest import LIVING, OUTDOOR, add_shutter, mock_moves

WEATHER = "weather.test"


def entity_id(hass: HomeAssistant, entry, subentry_id: str | None, domain: str, key: str) -> str:
    unique = f"{entry.entry_id}_{subentry_id}_{key}" if subentry_id else f"{entry.entry_id}_{key}"
    return er.async_get(hass).async_get_entity_id(domain, DOMAIN, unique)


async def setup_forecast(hass: HomeAssistant, forecast: list[dict]) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="House",
        data={"outdoor_temperature": OUTDOOR, "weather": WEATHER},
        options={**DEFAULT_OPTIONS, "close_delay": 0, "hot_day": 28},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    async def get_forecasts(call: ServiceCall) -> dict:
        return {call.data["entity_id"]: {"forecast": forecast}}

    hass.services.async_register(
        "weather",
        "get_forecasts",
        get_forecasts,
        supports_response=SupportsResponse.ONLY,
    )
    return entry


async def test_forecast_entities_and_hot_mild_days(hass: HomeAssistant, covers, monkeypatch, freezer) -> None:
    freezer.move_to("2026-11-18 10:00:00+01:00")
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    monkeypatch.setattr(SunPosition, "at", classmethod(lambda cls, *args: SunPosition(180, 35)))
    hass.states.async_set(WEATHER, "sunny", {"friendly_name": "Test weather"})
    hass.states.async_set(OUTDOOR, "15", {"device_class": "temperature", "unit_of_measurement": "°C"})

    forecast = [{"datetime": "2026-11-18T12:00:00+01:00", "temperature": 30}]
    entry = await setup_forecast(hass, forecast)
    response = await hass.services.async_call(
        "weather",
        "get_forecasts",
        {"entity_id": WEATHER, "type": "daily"},
        blocking=True,
        return_response=True,
    )
    assert response == {WEATHER: {"forecast": forecast}}
    await entry.runtime_data.async_refresh_forecast()
    await hass.async_block_till_done()
    calls = mock_moves(hass)
    await add_shutter(hass, entry, LIVING, azimuth=180, shading_position=30)
    await entry.runtime_data.async_tick()

    assert hass.states.get(entity_id(hass, entry, None, "sensor", "forecast_max")).state == "30.0"
    hot = hass.states.get(entity_id(hass, entry, None, "binary_sensor", "hot_day"))
    assert hot.state == "on" and hot.attributes["forecast_max"] == 30
    assert calls and calls[-1].data["position"] == 30

    calls.clear()
    forecast[0]["temperature"] = 20
    await entry.runtime_data.async_refresh_forecast()
    await entry.runtime_data.async_tick()
    assert hass.states.get(entity_id(hass, entry, None, "sensor", "forecast_max")).state == "20.0"
    assert hass.states.get(entity_id(hass, entry, None, "binary_sensor", "hot_day")).state == "off"
    assert not calls


async def test_empty_sun_option_stores_none_and_switches_hot_day_off(hass: HomeAssistant, covers) -> None:
    hass.states.async_set(WEATHER, "sunny")
    forecast = [{"datetime": "2026-11-18T12:00:00+01:00", "temperature": 30}]
    entry = await setup_forecast(hass, forecast)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "sun"})
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "sunny_threshold": 60,
            "max_incidence": 85,
            "heat_outdoor": 22,
            "heat_room": 24,
            "close_delay": 5,
            "open_delay": 20,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["hot_day"] is None
    assert entry.runtime_data.sun_settings().hot_day is None
    assert hass.states.get(entity_id(hass, entry, None, "binary_sensor", "hot_day")).state == "off"


async def test_forecast_read_when_the_weather_entity_appears(hass: HomeAssistant, covers) -> None:
    """The weather integration may start later: the forecast is read once its entity is there (#67)."""
    today = dt_util.now().date().isoformat()
    entry = await setup_forecast(hass, [{"datetime": f"{today}T12:00:00", "temperature": 30}])
    await hass.async_block_till_done()
    assert entry.runtime_data.forecast_max is None  # no weather entity yet

    hass.states.async_set(WEATHER, "sunny")
    await hass.async_block_till_done()
    assert entry.runtime_data.forecast_max == 30
    assert hass.states.get(entity_id(hass, entry, None, "sensor", "forecast_max")).state == "30.0"
