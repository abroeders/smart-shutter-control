"""Window and door contacts in Home Assistant: lockout, ventilation and the one-minute hold."""

from datetime import timedelta

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.smart_shutter_control.const import (
    CONF_LOCKOUT_POSITION,
    CONF_OPENED_CONTACT,
    CONF_TILTED_CONTACT,
    CONF_VENTILATION_POSITION,
)

from .conftest import LIVING, OUTDOOR, add_shutter, mock_moves, setup_base

DOOR = "binary_sensor.door"
TILTED = "binary_sensor.window_tilted"


@pytest.fixture
async def amsterdam(hass: HomeAssistant, freezer):
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    hass.config.latitude, hass.config.longitude = 52.0, 5.0
    return freezer


def eid(hass: HomeAssistant, entry, domain: str, key: str, shutter: bool = True) -> str:
    sub = next(iter(entry.subentries)) if shutter else None
    unique = f"{entry.entry_id}_{sub}_{key}" if sub else f"{entry.entry_id}_{key}"
    return er.async_get(hass).async_get_entity_id(domain, "smart_shutter_control", unique)


def report(hass: HomeAssistant, position: int) -> None:
    hass.states.async_set(
        LIVING,
        "closed" if position == 0 else "open",
        {"current_position": position, "supported_features": 15},
    )


async def tick(hass: HomeAssistant, entry) -> None:
    await entry.runtime_data.async_tick()
    await hass.async_block_till_done()


async def configure_contacts(hass: HomeAssistant, entry, subentry, **values) -> None:
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "contacts"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_LOCKOUT_POSITION: 100, **values},
    )
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()


async def test_contacts_step_saves_and_clears_optional_fields(hass: HomeAssistant, covers) -> None:
    hass.states.async_set(DOOR, "off")
    hass.states.async_set(TILTED, "off")
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    subentry = next(iter(entry.subentries.values()))

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "contacts"}
    )
    assert result["step_id"] == "contacts"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_OPENED_CONTACT: DOOR,
            CONF_TILTED_CONTACT: TILTED,
            CONF_LOCKOUT_POSITION: 90,
            CONF_VENTILATION_POSITION: 20,
        },
    )
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()
    data = entry.subentries[subentry.subentry_id].data
    assert data[CONF_OPENED_CONTACT] == DOOR
    assert data[CONF_TILTED_CONTACT] == TILTED
    assert data[CONF_LOCKOUT_POSITION] == 90
    assert data[CONF_VENTILATION_POSITION] == 20

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "contacts"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_LOCKOUT_POSITION: 80}
    )
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()
    data = entry.subentries[subentry.subentry_id].data
    assert data[CONF_LOCKOUT_POSITION] == 80
    assert CONF_OPENED_CONTACT not in data
    assert CONF_TILTED_CONTACT not in data
    assert CONF_VENTILATION_POSITION not in data


async def test_door_open_raises_closed_shutter_with_lockout_reason(
    hass: HomeAssistant, covers, amsterdam
) -> None:
    amsterdam.move_to("2026-11-18 23:00:00+01:00")
    report(hass, 0)
    hass.states.async_set(DOOR, "off")
    entry = await setup_base(hass)
    calls = mock_moves(hass)
    await add_shutter(hass, entry, LIVING)
    subentry = next(iter(entry.subentries.values()))
    await configure_contacts(hass, entry, subentry, opened_contact=DOOR)
    calls.clear()

    hass.states.async_set(DOOR, "on")
    await hass.async_block_till_done()
    assert calls[-1].data["position"] == 100
    reason = hass.states.get(eid(hass, entry, "sensor", "reason"))
    assert reason.state == "lockout"
    contacts = next(e for e in reason.attributes["decision"] if e["rule"] == "contacts")
    assert contacts["applied"] and contacts["why"] == "opened"


async def test_door_open_ends_running_manual_pause(hass: HomeAssistant, covers, amsterdam) -> None:
    amsterdam.move_to("2026-11-18 23:00:00+01:00")
    report(hass, 0)
    hass.states.async_set(DOOR, "off")
    entry = await setup_base(hass)
    calls = mock_moves(hass)
    await add_shutter(hass, entry, LIVING)
    subentry = next(iter(entry.subentries.values()))
    await configure_contacts(hass, entry, subentry, opened_contact=DOOR)
    calls.clear()

    report(hass, 40)
    await hass.async_block_till_done()
    assert hass.states.get(eid(hass, entry, "binary_sensor", "manual_pause")).state == "on"
    calls.clear()

    hass.states.async_set(DOOR, "on")
    await hass.async_block_till_done()
    assert hass.states.get(eid(hass, entry, "binary_sensor", "manual_pause")).state == "off"
    assert calls[-1].data["position"] == 100
    assert hass.states.get(eid(hass, entry, "sensor", "reason")).state == "lockout"


async def test_shutter_returns_to_rules_one_minute_after_door_closes(
    hass: HomeAssistant, covers, amsterdam
) -> None:
    amsterdam.move_to("2026-11-18 23:00:00+01:00")
    report(hass, 0)
    hass.states.async_set(DOOR, "off")
    entry = await setup_base(hass)
    calls = mock_moves(hass)
    await add_shutter(hass, entry, LIVING)
    subentry = next(iter(entry.subentries.values()))
    await configure_contacts(hass, entry, subentry, opened_contact=DOOR)

    hass.states.async_set(DOOR, "on")
    await hass.async_block_till_done()
    assert calls[-1].data["position"] == 100
    report(hass, 100)
    await hass.async_block_till_done()
    calls.clear()

    hass.states.async_set(DOOR, "off")
    await hass.async_block_till_done()
    amsterdam.tick(timedelta(seconds=61))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert calls[-1].data["position"] == 0


async def test_frost_and_integration_pause_leave_shutter_alone(
    hass: HomeAssistant, covers, amsterdam
) -> None:
    amsterdam.move_to("2026-11-18 23:00:00+01:00")
    report(hass, 0)
    hass.states.async_set(DOOR, "off")
    hass.states.async_set(OUTDOOR, "-3", {"device_class": "temperature", "unit_of_measurement": "°C"})
    entry = await setup_base(hass)
    calls = mock_moves(hass)
    await add_shutter(hass, entry, LIVING)
    subentry = next(iter(entry.subentries.values()))
    await configure_contacts(hass, entry, subentry, opened_contact=DOOR)
    calls.clear()

    hass.states.async_set(DOOR, "on")
    await hass.async_block_till_done()
    assert not calls
    assert hass.states.get(eid(hass, entry, "sensor", "reason")).state == "frost"

    hass.states.async_set(OUTDOOR, "12", {"device_class": "temperature", "unit_of_measurement": "°C"})
    await hass.async_block_till_done()
    switch = eid(hass, entry, "switch", "automatic_all", shutter=False)
    await hass.services.async_call("switch", "turn_off", {"entity_id": switch}, blocking=True)
    calls.clear()
    report(hass, 0)
    await hass.async_block_till_done()

    hass.states.async_set(DOOR, "on")
    await tick(hass, entry)
    assert not calls
    assert hass.states.get(eid(hass, entry, "sensor", "reason")).state == "paused"


async def test_tilted_contact_gives_the_slit(hass: HomeAssistant, covers, amsterdam) -> None:
    amsterdam.move_to("2026-11-18 23:00:00+01:00")
    report(hass, 0)
    hass.states.async_set(TILTED, "off")
    entry = await setup_base(hass)
    calls = mock_moves(hass)
    await add_shutter(hass, entry, LIVING)
    subentry = next(iter(entry.subentries.values()))
    await configure_contacts(hass, entry, subentry, tilted_contact=TILTED)

    hass.states.async_set(TILTED, "on")
    await hass.async_block_till_done()
    assert calls[-1].data["position"] == 20
    reason = hass.states.get(eid(hass, entry, "sensor", "reason"))
    assert reason.state == "ventilation"
    contacts = next(e for e in reason.attributes["decision"] if e["rule"] == "contacts")
    assert contacts["applied"] and contacts["why"] == "tilted"
