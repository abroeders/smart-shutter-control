"""Heat protection in Home Assistant: a sunny, warm afternoon lowers a south shutter, not a north one."""

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.smart_shutter_control.core.sun import SunPosition

from .conftest import BEDROOM, LIVING, OUTDOOR, add_shutter, setup_base


def entity_id(hass: HomeAssistant, entry, subentry_id: str | None, domain: str, key: str) -> str:
    unique = f"{entry.entry_id}_{subentry_id}_{key}" if subentry_id else f"{entry.entry_id}_{key}"
    return er.async_get(hass).async_get_entity_id(domain, "smart_shutter_control", unique)


async def test_sun_options(hass: HomeAssistant, covers) -> None:
    entry = await setup_base(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "sun"})
    assert result["step_id"] == "sun"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "sunny_threshold": 50,
            "max_incidence": 80,
            "heat_outdoor": 20,
            "heat_room": 23,
            "close_delay": 0,
            "open_delay": 10,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.runtime_data.sun_settings().close_delay == 0


async def test_sunny_afternoon(hass: HomeAssistant, covers, monkeypatch, freezer) -> None:
    freezer.move_to("2026-11-18 13:00:00+01:00")  # the day phase
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    monkeypatch.setattr(SunPosition, "at", classmethod(lambda cls, *args: SunPosition(200, 35)))
    hass.states.async_set(OUTDOOR, "26.0", {"device_class": "temperature", "unit_of_measurement": "°C"})
    entry = await setup_base(hass)
    hass.config_entries.async_update_entry(entry, options={**entry.options, "close_delay": 0})
    await hass.async_block_till_done()
    calls = async_mock_service(hass, "cover", "set_cover_position")
    await add_shutter(hass, entry, LIVING, azimuth=190, shading_position=30)
    await add_shutter(hass, entry, BEDROOM, azimuth=10)
    await entry.runtime_data.async_tick()

    assert calls and all(c.data["entity_id"] == LIVING for c in calls)
    assert calls[-1].data["position"] == 30
    south = next(s.subentry_id for s in entry.subentries.values() if s.data["cover"] == LIVING)
    north = next(s.subentry_id for s in entry.subentries.values() if s.data["cover"] == BEDROOM)
    assert hass.states.get(entity_id(hass, entry, south, "binary_sensor", "sun_on_window")).state == "on"
    assert hass.states.get(entity_id(hass, entry, north, "binary_sensor", "sun_on_window")).state == "off"
    assert hass.states.get(entity_id(hass, entry, south, "sensor", "reason")).state == "sun"
    assert hass.states.get(entity_id(hass, entry, None, "binary_sensor", "sunny")).state == "on"
    assert (
        hass.states.get(entity_id(hass, entry, None, "sensor", "sun_factor")).attributes["source"]
        == "geometry"
    )

    calls.clear()
    switch = entity_id(hass, entry, south, "switch", "heat_protection")
    await hass.services.async_call("switch", "turn_off", {"entity_id": switch}, blocking=True)
    # without heat protection the day phase wants it open; the (mocked) shutter never left 100 %
    assert not calls
    assert hass.states.get(entity_id(hass, entry, south, "sensor", "reason")).state == "schedule"
