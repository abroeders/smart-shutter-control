"""Storm and frost in Home Assistant: only the ends in a storm, following the evening; no moves in frost."""

from datetime import timedelta

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.smart_shutter_control.const import DEFAULT_OPTIONS, DOMAIN

from .conftest import LIVING, OUTDOOR, add_shutter

GUST = "sensor.gust"


def report(hass: HomeAssistant, position: int) -> None:
    hass.states.async_set(
        LIVING,
        "closed" if position == 0 else "open",
        {"current_position": position, "supported_features": 15},
    )


def gust(hass: HomeAssistant, value: float) -> None:
    hass.states.async_set(GUST, str(value), {"device_class": "wind_speed", "unit_of_measurement": "km/h"})


@pytest.fixture
async def amsterdam(hass: HomeAssistant, freezer):
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    hass.config.latitude, hass.config.longitude = 52.0, 5.0
    return freezer


async def setup(hass: HomeAssistant, **options) -> MockConfigEntry:
    gust(hass, 20)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="House",
        data={"outdoor_temperature": OUTDOOR, "wind_gust": GUST},
        options={**DEFAULT_OPTIONS, "storm_gust_limit": 70, **options},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def eid(hass: HomeAssistant, entry, domain: str, key: str, shutter: bool = True) -> str:
    sub = next(iter(entry.subentries)) if shutter else None
    unique = f"{entry.entry_id}_{sub}_{key}" if sub else f"{entry.entry_id}_{key}"
    return er.async_get(hass).async_get_entity_id(domain, DOMAIN, unique)


async def tick(hass: HomeAssistant, entry) -> None:
    await entry.runtime_data.async_tick()
    await hass.async_block_till_done()


async def test_storm_only_ends_and_the_evening(hass: HomeAssistant, covers, amsterdam) -> None:
    amsterdam.move_to("2026-11-18 12:00:00+01:00")
    report(hass, 100)
    entry = await setup(hass)
    calls = async_mock_service(hass, "cover", "set_cover_position")
    await add_shutter(hass, entry, LIVING)
    gust(hass, 75)  # storm
    await tick(hass, entry)
    storm = hass.states.get(eid(hass, entry, "binary_sensor", "storm", shutter=False))
    assert storm.state == "on" and storm.attributes["gust"] == 75  # also for the trees in the card
    assert hass.states.get(eid(hass, entry, "sensor", "reason")).state == "storm"
    assert not calls  # open by day: already at the open end

    report(hass, 40)  # someone lowers it by the wall switch: to an end within seconds
    await hass.async_block_till_done()
    amsterdam.tick(timedelta(seconds=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    # paused by the manual action, no rule wants a position: the end nearest to 40 % is closed
    assert calls[-1].data["position"] == 0
    report(hass, 0)
    await hass.async_block_till_done()

    number = eid(hass, entry, "number", "opening")
    await hass.services.async_call("number", "set_value", {"entity_id": number, "value": 70}, blocking=True)
    assert calls[-1].data["position"] == 100  # through our own entities only the ends exist
    report(hass, 100)
    await hass.async_block_till_done()

    gust(hass, 72)
    amsterdam.move_to("2026-11-18 23:00:00+01:00")  # the evening starts during the storm: closed
    await tick(hass, entry)
    assert all(c.data["position"] in (0, 100) for c in calls)
    assert calls[-1].data["position"] == 0  # the pause ended with the phase; the night wants it closed


async def test_locked_open_closes_when_the_evening_starts(hass: HomeAssistant, covers, amsterdam) -> None:
    amsterdam.move_to("2026-11-18 16:00:00+01:00")
    report(hass, 100)
    entry = await setup(hass)
    calls = async_mock_service(hass, "cover", "set_cover_position")
    await add_shutter(hass, entry, LIVING)
    gust(hass, 80)
    await tick(hass, entry)
    assert not calls
    amsterdam.move_to("2026-11-18 22:00:00+01:00")
    gust(hass, 80)
    await tick(hass, entry)
    assert calls[-1].data["position"] == 0


async def test_no_calibration_during_a_storm(hass: HomeAssistant, covers, amsterdam) -> None:
    amsterdam.move_to("2026-11-18 12:00:00+01:00")
    entry = await setup(hass)
    await add_shutter(hass, entry, LIVING)
    gust(hass, 90)
    await tick(hass, entry)
    sub = next(iter(entry.subentries))
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"), context={"source": "reconfigure", "subentry_id": sub}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "calibrate"}
    )
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "storm"


async def test_frost_does_not_move(hass: HomeAssistant, covers, amsterdam) -> None:
    amsterdam.move_to("2026-11-18 23:00:00+01:00")  # night: the schedule wants closed
    report(hass, 100)
    hass.states.async_set(OUTDOOR, "-3", {"device_class": "temperature", "unit_of_measurement": "°C"})
    entry = await setup(hass)
    calls = async_mock_service(hass, "cover", "set_cover_position")
    await add_shutter(hass, entry, LIVING)
    await tick(hass, entry)
    assert not calls
    assert hass.states.get(eid(hass, entry, "binary_sensor", "frost", shutter=False)).state == "on"
    assert hass.states.get(eid(hass, entry, "sensor", "reason")).state == "frost"


async def test_old_storm_limit_becomes_the_gust_limit(hass: HomeAssistant, covers) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN, title="House", data={"outdoor_temperature": OUTDOOR}, options={"storm_limit": 65}
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.storm.gust_limit == 65


async def test_winter_cold_day_and_evening(hass: HomeAssistant, covers, amsterdam) -> None:
    amsterdam.move_to("2026-11-18 12:00:00+01:00")
    report(hass, 100)
    hass.states.async_set(OUTDOOR, "-6", {"device_class": "temperature", "unit_of_measurement": "°C"})
    entry = await setup(hass, frost_limit=-20)  # no frost lock for this test
    calls = async_mock_service(hass, "cover", "set_cover_position")
    await add_shutter(hass, entry, LIVING)
    select = eid(hass, entry, "select", "winter_mode", shutter=False)
    await hass.services.async_call(
        "select", "select_option", {"entity_id": select, "option": "on"}, blocking=True
    )
    assert hass.states.get(eid(hass, entry, "binary_sensor", "winter", shutter=False)).state == "on"
    assert calls[-1].data["position"] == 0  # very cold: closed all day
    assert hass.states.get(eid(hass, entry, "sensor", "reason")).state == "winter"
    report(hass, 0)
    await hass.async_block_till_done()

    # milder in the evening: the dusk position does not raise the closed shutter
    calls.clear()
    hass.states.async_set(OUTDOOR, "2", {"device_class": "temperature", "unit_of_measurement": "°C"})
    amsterdam.move_to("2026-11-18 16:45:00+01:00")
    await tick(hass, entry)
    assert hass.states.get(eid(hass, entry, "sensor", "phase")).state == "dusk"
    assert not calls
