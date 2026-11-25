"""Locks from an automation (#52) in Home Assistant: the action, the select, how a lock ends, the floors."""

from datetime import UTC, datetime, timedelta

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.smart_shutter_control.const import DOMAIN

from .conftest import BEDROOM, LIVING, add_shutter, mock_moves, setup_base
from .test_contacts import configure_contacts, report

DOOR = "binary_sensor.door"
NOON = "2026-11-18 12:00:00+01:00"  # a Wednesday: the day phase wants the shutters open


@pytest.fixture
async def noon(hass: HomeAssistant, freezer):
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    hass.config.latitude, hass.config.longitude = 52.0, 5.0
    freezer.move_to(NOON)
    return freezer


def subentry_of(entry, cover: str) -> str:
    return next(i for i, c in entry.runtime_data.shutters.items() if c.config.cover == cover)


def entity(hass: HomeAssistant, entry, domain: str, key: str, cover: str = LIVING) -> str:
    unique = f"{entry.entry_id}_{subentry_of(entry, cover)}_{key}"
    return er.async_get(hass).async_get_entity_id(domain, DOMAIN, unique)


def _device_id(hass: HomeAssistant, entry, identifier: tuple[str, str]) -> str:
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    return next(d.id for d in devices if identifier in d.identifiers)


def device_of(hass: HomeAssistant, entry, cover: str = LIVING) -> str:
    wanted = (DOMAIN, subentry_of(entry, cover))
    return _device_id(hass, entry, wanted)


async def set_lock(hass: HomeAssistant, devices: list[str], mode: str, **fields) -> None:
    await hass.services.async_call(
        DOMAIN, "set_lock", {"device_id": devices, "mode": mode, **fields}, blocking=True
    )
    await hass.async_block_till_done()


def lock_state(hass: HomeAssistant, entry, cover: str = LIVING):
    return hass.states.get(entity(hass, entry, "select", "lock", cover))


async def shutter(hass: HomeAssistant, **extra):
    entry = await setup_base(hass)
    calls = mock_moves(hass)
    await add_shutter(hass, entry, LIVING, **extra)
    await entry.runtime_data.async_tick()
    calls.clear()
    return entry, calls


async def test_force_closed_on_one_device_without_duration(hass: HomeAssistant, covers, noon) -> None:
    entry, calls = await shutter(hass)
    assert lock_state(hass, entry).state == "none"

    await set_lock(hass, [device_of(hass, entry)], "force_closed")
    assert calls[-1].data["position"] == 0
    state = lock_state(hass, entry)
    assert state.state == "force_closed" and state.attributes["until"] is None
    assert hass.states.get(entity(hass, entry, "sensor", "reason")).state == "locked"

    await set_lock(hass, [device_of(hass, entry)], "none")
    assert lock_state(hass, entry).state == "none"
    assert hass.states.get(entity(hass, entry, "sensor", "reason")).state == "schedule"


async def test_force_closed_with_a_duration_has_an_end_time(hass: HomeAssistant, covers, noon) -> None:
    entry, calls = await shutter(hass)
    await set_lock(hass, [device_of(hass, entry)], "force_closed", duration={"hours": 2})
    state = lock_state(hass, entry)
    assert datetime.fromisoformat(state.attributes["until"]) == datetime.now(UTC) + timedelta(hours=2)

    noon.move_to("2026-11-18 14:00:01+01:00")
    await entry.runtime_data.async_tick()
    await hass.async_block_till_done()
    assert lock_state(hass, entry).state == "none"  # expired: back to what automatic control wants


async def test_two_devices_with_and_without_a_duration(hass: HomeAssistant, covers, noon) -> None:
    entry = await setup_base(hass)
    mock_moves(hass)
    await add_shutter(hass, entry, LIVING)
    await add_shutter(hass, entry, BEDROOM)
    devices = [device_of(hass, entry, LIVING), device_of(hass, entry, BEDROOM)]

    await set_lock(hass, devices, "hold")
    assert [lock_state(hass, entry, c).state for c in (LIVING, BEDROOM)] == ["hold", "hold"]
    assert lock_state(hass, entry).attributes["until"] is None

    await set_lock(hass, devices, "force_open", duration={"minutes": 30})
    expected = datetime.now(UTC) + timedelta(minutes=30)
    for cover in (LIVING, BEDROOM):
        state = lock_state(hass, entry, cover)
        assert state.state == "force_open"
        assert datetime.fromisoformat(state.attributes["until"]) == expected


async def test_an_unknown_or_non_shutter_device_raises(hass: HomeAssistant, covers, noon) -> None:
    entry, calls = await shutter(hass)
    with pytest.raises(ServiceValidationError):
        await set_lock(hass, ["no_such_device"], "hold")

    base_id = _device_id(hass, entry, (DOMAIN, entry.entry_id))
    with pytest.raises(ServiceValidationError):
        await set_lock(hass, [base_id], "hold")

    with pytest.raises(ServiceValidationError):  # nothing is locked when one of the devices is wrong
        await set_lock(hass, [device_of(hass, entry), "no_such_device"], "force_closed")
    assert lock_state(hass, entry).state == "none" and not calls


async def test_select_shows_and_sets_the_lock(hass: HomeAssistant, covers, noon) -> None:
    entry, calls = await shutter(hass)
    select = entity(hass, entry, "select", "lock")
    assert hass.states.get(select).attributes["options"] == ["none", "hold", "force_open", "force_closed"]

    await hass.services.async_call(
        "select", "select_option", {"entity_id": select, "option": "force_closed"}, blocking=True
    )
    await hass.async_block_till_done()
    assert (
        hass.states.get(select).state == "force_closed"
        and hass.states.get(select).attributes["until"] is None
    )
    assert calls[-1].data["position"] == 0

    await set_lock(hass, [device_of(hass, entry)], "hold")
    assert hass.states.get(select).state == "hold"


async def test_a_manual_cover_report_ends_the_lock(hass: HomeAssistant, covers, noon) -> None:
    entry, calls = await shutter(hass)
    await set_lock(hass, [device_of(hass, entry)], "hold")
    assert lock_state(hass, entry).state == "hold" and not calls

    report(hass, 40)  # a wall switch
    await hass.async_block_till_done()
    assert lock_state(hass, entry).state == "none"
    assert hass.states.get(entity(hass, entry, "binary_sensor", "manual_pause")).state == "on"
    await entry.runtime_data.async_tick()  # the reason follows at the next evaluation
    assert hass.states.get(entity(hass, entry, "sensor", "reason")).state == "manual"


async def test_the_resume_button_ends_the_lock(hass: HomeAssistant, covers, noon) -> None:
    entry, calls = await shutter(hass)
    await set_lock(hass, [device_of(hass, entry)], "force_closed")
    assert lock_state(hass, entry).state == "force_closed"

    await hass.services.async_call(
        "button", "press", {"entity_id": entity(hass, entry, "button", "resume")}, blocking=True
    )
    await hass.async_block_till_done()
    assert lock_state(hass, entry).state == "none"
    assert hass.states.get(entity(hass, entry, "sensor", "reason")).state == "schedule"


async def test_the_lock_survives_a_reload(hass: HomeAssistant, covers, noon) -> None:
    entry, calls = await shutter(hass)
    await set_lock(hass, [device_of(hass, entry)], "force_closed", duration={"hours": 2})
    until = lock_state(hass, entry).attributes["until"]

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    state = lock_state(hass, entry)
    assert state.state == "force_closed" and state.attributes["until"] == until


async def test_the_open_door_floor_still_raises_a_force_closed_shutter(
    hass: HomeAssistant, covers, noon
) -> None:
    report(hass, 0)
    hass.states.async_set(DOOR, "off")
    entry, calls = await shutter(hass)
    subentry = entry.subentries[subentry_of(entry, LIVING)]
    await configure_contacts(hass, entry, subentry, opened_contact=DOOR)
    await set_lock(hass, [device_of(hass, entry)], "force_closed")
    assert hass.states.get(entity(hass, entry, "sensor", "reason")).state == "locked"
    calls.clear()

    hass.states.async_set(DOOR, "on")
    await hass.async_block_till_done()
    assert calls[-1].data["position"] == 100
    assert hass.states.get(entity(hass, entry, "sensor", "reason")).state == "lockout"
    assert lock_state(hass, entry).state == "force_closed"  # the lock stays: the door floor is on top


async def test_reason_locked_with_the_mode_in_the_trace(hass: HomeAssistant, covers, noon) -> None:
    entry, calls = await shutter(hass)
    await set_lock(hass, [device_of(hass, entry)], "hold")
    reason = hass.states.get(entity(hass, entry, "sensor", "reason"))
    assert reason.state == "locked"
    rule = next(e for e in reason.attributes["decision"] if e["rule"] == "lock")
    assert rule["applied"] and rule["why"] == "locked" and rule["values"] == {"mode": "hold"}


async def test_force_open_goes_to_100_above_a_lower_maximum_position(
    hass: HomeAssistant, covers, noon
) -> None:
    report(hass, 60)
    entry, calls = await shutter(hass, max_position=60)
    assert entry.runtime_data.shutters[subentry_of(entry, LIVING)].max_position == 60

    await set_lock(hass, [device_of(hass, entry)], "force_open")
    assert calls[-1].data["position"] == 100
    assert hass.states.get(entity(hass, entry, "sensor", "reason")).state == "locked"


async def test_an_expired_lock_ends_while_automatic_control_is_off(
    hass: HomeAssistant, covers, noon, freezer
) -> None:
    """Review of #52: the select must not keep showing a lock whose time is over."""
    entry, _calls = await shutter(hass)
    await set_lock(hass, [device_of(hass, entry)], "force_closed", duration={"minutes": 30})
    controller = next(iter(entry.runtime_data.shutters.values()))
    controller.automatic = False
    freezer.tick(45 * 60)
    await entry.runtime_data.async_tick()
    await hass.async_block_till_done()
    assert lock_state(hass, entry).state == "none"
    assert controller.store.get(controller.id, "lock") == {"mode": "none", "until": None}
