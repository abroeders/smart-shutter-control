"""Schedules and manual operation in Home Assistant: a morning, overrides, holidays, pauses, sleep-in."""

from datetime import timedelta

import pytest
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_fire_time_changed, async_mock_service

from .conftest import LIVING, add_shutter, setup_base


def eid(hass: HomeAssistant, entry, domain: str, key: str, shutter: bool = True) -> str:
    sub = next(iter(entry.subentries)) if shutter else None
    unique = f"{entry.entry_id}_{sub}_{key}" if sub else f"{entry.entry_id}_{key}"
    return er.async_get(hass).async_get_entity_id(domain, "smart_shutter_control", unique)


def report(hass: HomeAssistant, position: int) -> None:
    """The physical shutter reports a position (moved by someone else, or arrived)."""
    hass.states.async_set(
        LIVING,
        "closed" if position == 0 else "open",
        {"current_position": position, "supported_features": 15},
    )


@pytest.fixture
async def amsterdam(hass: HomeAssistant, freezer):
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    hass.config.latitude, hass.config.longitude = 52.0, 5.0
    return freezer


async def tick(hass: HomeAssistant, entry) -> None:
    await entry.runtime_data.async_tick()
    await hass.async_block_till_done()


async def test_a_weekday_morning(hass: HomeAssistant, covers, amsterdam) -> None:
    amsterdam.move_to("2026-11-18 07:50:00+01:00")
    report(hass, 0)
    entry = await setup_base(hass)
    calls = async_mock_service(hass, "cover", "set_cover_position")
    await add_shutter(hass, entry, LIVING)
    assert not calls and hass.states.get(eid(hass, entry, "sensor", "phase")).state == "night"
    next_action = hass.states.get(eid(hass, entry, "sensor", "next_action"))
    assert next_action.attributes["phase"] == "slit" and next_action.state.startswith("2026-11-18T07:00:00")
    amsterdam.move_to("2026-11-18 08:00:30+01:00")
    await tick(hass, entry)
    assert calls[-1].data["position"] == 20  # the slit (module position, not calibrated)
    report(hass, 20)  # the shutter arrives
    await hass.async_block_till_done()
    amsterdam.move_to("2026-11-18 08:30:30+01:00")
    await tick(hass, entry)
    assert calls[-1].data["position"] == 100
    report(hass, 100)
    await hass.async_block_till_done()
    amsterdam.move_to("2026-11-18 23:00:00+01:00")
    await tick(hass, entry)
    assert (
        calls[-1].data["position"] == 0
        and hass.states.get(eid(hass, entry, "sensor", "phase")).state == "night"
    )


async def test_base_schedule_and_overrides(hass: HomeAssistant, covers, amsterdam) -> None:
    amsterdam.move_to("2026-11-18 07:50:00+01:00")
    entry = await setup_base(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "schedule"}
    )
    assert result["step_id"] == "schedule"
    base = {k: v for k, v in result["data_schema"]({}).items()}
    base["weekday_open"] = "09:00:00"
    result = await hass.config_entries.options.async_configure(result["flow_id"], base)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    await add_shutter(hass, entry, LIVING)
    sub = next(iter(entry.subentries))
    controller = entry.runtime_data.shutters[sub]
    assert controller.schedule_values["weekday_open"] == "09:00:00" and controller.overrides() == []

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"), context={"source": "reconfigure", "subentry_id": sub}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "schedule"}
    )
    assert result["step_id"] == "schedule"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"weekday_open": "08:15:00", "slit_phase": "off", "dusk_phase": "inherit"}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()
    controller = entry.runtime_data.shutters[sub]
    assert controller.schedule_values["weekday_open"] == "08:15:00"
    assert controller.overrides() == ["slit_phase", "weekday_open"]
    assert controller.next_change().phase.value == "day"  # no slit phase any more

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"), context={"source": "reconfigure", "subentry_id": sub}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "schedule_reset"}
    )
    await hass.async_block_till_done()
    assert entry.runtime_data.shutters[sub].overrides() == []


async def test_holidays_from_a_calendar_and_the_list(hass: HomeAssistant, covers, amsterdam) -> None:
    amsterdam.move_to("2026-12-23 12:00:00+01:00")

    async def get_events(call: ServiceCall):
        return {
            "calendar.holidays": {
                "events": [{"start": "2026-12-25", "end": "2026-12-26", "summary": "Christmas"}]
            }
        }

    hass.services.async_register(
        "calendar", "get_events", get_events, supports_response=SupportsResponse.ONLY
    )
    entry = await setup_base(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "holidays"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"weekend_days": ["sat", "sun"], "holidays_extra": "12-24 Eve\nnot a date"}
    )
    assert result["errors"] == {"holidays_extra": "bad_dates"}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "holiday_calendar": "calendar.holidays",
            "weekend_days": ["sat", "sun"],
            "holidays_extra": "12-24 Eve",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    calendar = entry.runtime_data.calendar
    from datetime import date

    assert calendar.holiday(date(2026, 12, 25)) == "Christmas" and calendar.is_free(date(2026, 12, 24))
    amsterdam.move_to("2026-12-24 12:00:00+01:00")
    await add_shutter(hass, entry, LIVING)
    assert hass.states.get(eid(hass, entry, "binary_sensor", "holiday", shutter=False)).state == "on"

    # disable a calendar holiday: it counts as a normal day from then on
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "holidays"}
    )
    assert "holidays_disabled" in result["data_schema"].schema
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "holiday_calendar": "calendar.holidays",
            "weekend_days": ["sat", "sun"],
            "holidays_extra": "12-24 Eve",
            "holidays_disabled": ["Christmas"],
        },
    )
    await hass.async_block_till_done()
    assert entry.runtime_data.calendar.holiday(date(2026, 12, 25)) is None


async def test_manual_pause_and_back_to_automatic_by_hand(hass: HomeAssistant, covers, amsterdam) -> None:
    amsterdam.move_to("2026-11-18 12:00:00+01:00")
    entry = await setup_base(hass)
    calls = async_mock_service(hass, "cover", "set_cover_position")
    await add_shutter(hass, entry, LIVING)
    report(hass, 40)  # someone lowers it by hand
    await hass.async_block_till_done()
    pause = hass.states.get(eid(hass, entry, "binary_sensor", "manual_pause"))
    assert pause.state == "on" and pause.attributes["until"] == "next phase"
    await tick(hass, entry)
    assert not calls and hass.states.get(eid(hass, entry, "sensor", "reason")).state == "manual"
    report(hass, 99)  # and back up by hand, close enough to the wanted 100 %
    await hass.async_block_till_done()
    amsterdam.tick(timedelta(seconds=20))
    await tick(hass, entry)
    assert hass.states.get(eid(hass, entry, "binary_sensor", "manual_pause")).state == "off"
    assert not calls  # resumed without moving


async def test_resume_button_moves_at_once(hass: HomeAssistant, covers, amsterdam) -> None:
    amsterdam.move_to("2026-11-18 12:00:00+01:00")
    entry = await setup_base(hass)
    calls = async_mock_service(hass, "cover", "set_cover_position")
    await add_shutter(hass, entry, LIVING)
    report(hass, 40)
    await hass.async_block_till_done()
    await tick(hass, entry)
    assert not calls
    await hass.services.async_call(
        "button", "press", {"entity_id": eid(hass, entry, "button", "resume")}, blocking=True
    )
    assert calls[-1].data["position"] == 100
    assert hass.states.get(eid(hass, entry, "binary_sensor", "manual_pause")).state == "off"


async def test_ignore_mode_moves_back(hass: HomeAssistant, covers, amsterdam) -> None:
    amsterdam.move_to("2026-11-18 12:00:00+01:00")
    entry = await setup_base(hass)
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, "schedule": {"manual_mode": "ignore"}}
    )
    await hass.async_block_till_done()
    calls = async_mock_service(hass, "cover", "set_cover_position")
    await add_shutter(hass, entry, LIVING)
    report(hass, 40)
    await hass.async_block_till_done()
    await tick(hass, entry)
    assert calls[-1].data["position"] == 100


async def test_sleep_in(hass: HomeAssistant, covers, amsterdam) -> None:
    amsterdam.move_to("2026-11-17 22:00:00+01:00")
    report(hass, 0)
    entry = await setup_base(hass)
    calls = async_mock_service(hass, "cover", "set_cover_position")
    await add_shutter(hass, entry, LIVING)
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": eid(hass, entry, "switch", "sleep_in_all", shutter=False)},
        blocking=True,
    )
    assert hass.states.get(eid(hass, entry, "switch", "sleep_in")).state == "on"
    amsterdam.move_to("2026-11-18 08:31:00+01:00")
    await tick(hass, entry)
    assert not calls and hass.states.get(eid(hass, entry, "sensor", "reason")).state == "sleep_in"
    report(hass, 30)  # opened by hand: sleep-in ends
    await hass.async_block_till_done()
    assert hass.states.get(eid(hass, entry, "switch", "sleep_in")).state == "off"
    async_fire_time_changed(hass)
