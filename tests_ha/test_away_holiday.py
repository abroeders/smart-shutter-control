"""Away and holiday (#51) in Home Assistant: options, presence entity, holiday switch and shifts."""

import json
from datetime import date, datetime, timedelta

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.smart_shutter_control.const import DEFAULT_OPTIONS, DOMAIN
from custom_components.smart_shutter_control.core.presence import RandomShift
from custom_components.smart_shutter_control.core.schedule import _sun_times
from custom_components.smart_shutter_control.diagnostics import async_get_config_entry_diagnostics

from .conftest import LIVING, OUTDOOR, add_shutter, mock_moves

NOON = "2026-11-18 12:00:00+01:00"  # a Wednesday
PRESENCE = "binary_sensor.somebody_home"
DELAY = 15  # min, the default


@pytest.fixture(autouse=True)
def _fresh_sun_times():
    """A test that fixes the sun's position must not leave its sunrise and sunset in the cache."""
    _sun_times.cache_clear()
    yield
    _sun_times.cache_clear()


@pytest.fixture
async def noon(hass: HomeAssistant, freezer):
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    hass.config.latitude, hass.config.longitude = 52.0, 5.0
    freezer.move_to(NOON)
    return freezer


async def setup(hass: HomeAssistant, presence: str | None = PRESENCE, **options) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="House",
        data={"outdoor_temperature": OUTDOOR},
        options={**DEFAULT_OPTIONS, "presence": presence, **options},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def base_entity(hass: HomeAssistant, entry, domain: str, key: str) -> str:
    return er.async_get(hass).async_get_entity_id(domain, DOMAIN, f"{entry.entry_id}_{key}")


def away(hass: HomeAssistant, entry):
    return hass.states.get(base_entity(hass, entry, "binary_sensor", "away"))


def holiday(hass: HomeAssistant, entry):
    return hass.states.get(base_entity(hass, entry, "switch", "holiday_mode"))


async def set_holiday(hass: HomeAssistant, entry, on: bool) -> None:
    await hass.services.async_call(
        "switch",
        "turn_on" if on else "turn_off",
        {"entity_id": base_entity(hass, entry, "switch", "holiday_mode")},
        blocking=True,
    )
    await hass.async_block_till_done()


async def later(hass: HomeAssistant, freezer, **delta) -> None:
    freezer.tick(timedelta(**delta))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


def shutter_entity(hass: HomeAssistant, entry, domain: str, key: str) -> str:
    sub = next(iter(entry.subentries))
    return er.async_get(hass).async_get_entity_id(domain, DOMAIN, f"{entry.entry_id}_{sub}_{key}")


def trace(hass: HomeAssistant, entry, rule: str) -> dict:
    reason = hass.states.get(shutter_entity(hass, entry, "sensor", "reason"))
    return next(e for e in reason.attributes["decision"] if e["rule"] == rule)


async def test_the_options_step_away(hass: HomeAssistant, covers) -> None:
    entry = await setup(hass, presence=None)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert "away" in result["menu_options"]
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "away"})
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "away"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"presence": "zone.home", "away_delay": 10, "away_heat_offset": 4, "holiday_shift": 20},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["presence"] == "zone.home"
    assert (entry.options["away_delay"], entry.options["away_heat_offset"]) == (10, 4)
    assert entry.options["holiday_shift"] == 20
    assert entry.runtime_data.sun_settings().away_offset == 4
    assert entry.options["heat_outdoor"] == DEFAULT_OPTIONS["heat_outdoor"]  # the other options stay


async def test_the_presence_entity_can_be_emptied_and_has_four_domains(hass: HomeAssistant, covers) -> None:
    entry = await setup(hass, presence="zone.home")
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "away"})
    with pytest.raises(InvalidData):
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            {"presence": "sensor.outdoor", "away_delay": 15, "away_heat_offset": 3, "holiday_shift": 30},
        )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"away_delay": 15, "away_heat_offset": 3, "holiday_shift": 30}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["presence"] is None and entry.runtime_data.presence is None


@pytest.mark.parametrize(
    ("entity", "home", "nobody"),
    [
        ("zone.home", "1", "0"),
        ("person.anna", "home", "not_home"),
        ("device_tracker.phone", "home", "not_home"),
        ("group.family", "home", "not_home"),
        ("group.family_on", "on", "off"),
        ("binary_sensor.somebody_home", "on", "off"),
    ],
)
async def test_nobody_home_turns_away_on_after_the_delay(
    hass: HomeAssistant, covers, noon, entity, home, nobody
) -> None:
    hass.states.async_set(entity, home)
    entry = await setup(hass, presence=entity)
    assert away(hass, entry).state == "off"

    hass.states.async_set(entity, nobody)
    await hass.async_block_till_done()
    assert away(hass, entry).state == "off"  # waiting for the delay
    await later(hass, noon, minutes=DELAY - 1)
    assert away(hass, entry).state == "off"
    await later(hass, noon, minutes=1, seconds=1)
    state = away(hass, entry)
    assert state.state == "on"
    assert datetime.fromisoformat(state.attributes["since"]) >= datetime.fromisoformat(NOON)

    hass.states.async_set(entity, home)  # coming home counts at once
    await hass.async_block_till_done()
    state = away(hass, entry)
    assert state.state == "off" and state.attributes["since"] is None


async def test_a_short_absence_does_not_count(hass: HomeAssistant, covers, noon) -> None:
    hass.states.async_set(PRESENCE, "on")
    entry = await setup(hass)
    hass.states.async_set(PRESENCE, "off")
    await hass.async_block_till_done()
    await later(hass, noon, minutes=10)
    hass.states.async_set(PRESENCE, "on")
    await hass.async_block_till_done()
    hass.states.async_set(PRESENCE, "off")
    await hass.async_block_till_done()

    await later(hass, noon, minutes=DELAY - 1)  # 25 min after the first departure, 14 after the last
    assert away(hass, entry).state == "off"
    await later(hass, noon, minutes=2)
    assert away(hass, entry).state == "on"


async def test_an_unavailable_presence_entity_counts_as_home(hass: HomeAssistant, covers, noon) -> None:
    hass.states.async_set(PRESENCE, "on")
    entry = await setup(hass)
    hass.states.async_set(PRESENCE, "unavailable")
    await hass.async_block_till_done()
    await later(hass, noon, minutes=2 * DELAY)
    assert away(hass, entry).state == "off"


async def test_nobody_home_at_start_waits_the_delay_from_the_start(hass: HomeAssistant, covers, noon) -> None:
    hass.states.async_set(PRESENCE, "off")
    entry = await setup(hass)
    assert away(hass, entry).state == "off"
    await later(hass, noon, minutes=DELAY, seconds=1)
    assert away(hass, entry).state == "on"


async def test_without_a_presence_entity_never_away(hass: HomeAssistant, covers, noon) -> None:
    entry = await setup(hass, presence=None)
    await later(hass, noon, hours=48)
    assert away(hass, entry).state == "off" and holiday(hass, entry).state == "off"

    await set_holiday(hass, entry, True)  # only holiday makes it away
    assert away(hass, entry).state == "on"
    await set_holiday(hass, entry, False)
    assert away(hass, entry).state == "off"


async def test_the_holiday_switch_turns_away_on_at_once(hass: HomeAssistant, covers, noon) -> None:
    hass.states.async_set(PRESENCE, "on")  # somebody is home
    entry = await setup(hass)
    assert holiday(hass, entry).state == "off"

    await set_holiday(hass, entry, True)
    assert holiday(hass, entry).state == "on" and away(hass, entry).state == "on"
    assert away(hass, entry).attributes["since"] is not None
    await set_holiday(hass, entry, False)
    assert holiday(hass, entry).state == "off" and away(hass, entry).state == "off"


async def test_holiday_is_never_switched_on_by_itself(hass: HomeAssistant, covers, noon) -> None:
    hass.states.async_set(PRESENCE, "off")
    entry = await setup(hass)
    await later(hass, noon, hours=24)
    assert away(hass, entry).state == "on" and holiday(hass, entry).state == "off"


async def test_away_lowers_the_heat_limits_in_the_trace(
    hass: HomeAssistant, covers, noon, monkeypatch
) -> None:
    from custom_components.smart_shutter_control.core.sun import SunPosition

    monkeypatch.setattr(SunPosition, "at", classmethod(lambda cls, *args: SunPosition(180, 35)))
    hass.states.async_set(OUTDOOR, "15", {"device_class": "temperature", "unit_of_measurement": "°C"})
    hass.states.async_set(PRESENCE, "on")
    entry = await setup(hass, close_delay=0)
    mock_moves(hass)
    await add_shutter(hass, entry, LIVING)
    await entry.runtime_data.async_tick()
    await hass.async_block_till_done()
    assert "away" not in trace(hass, entry, "heat")["values"]

    await set_holiday(hass, entry, True)
    values = trace(hass, entry, "heat")["values"]
    assert values["away"] is True and values["limit"] == DEFAULT_OPTIONS["heat_outdoor"] - 3


async def test_holiday_shifts_the_schedule_times(hass: HomeAssistant, covers, noon) -> None:
    entry = await setup(hass, presence=None)
    mock_moves(hass)
    await add_shutter(hass, entry, LIVING)
    await entry.runtime_data.async_tick()
    await hass.async_block_till_done()
    next_action = hass.states.get(shutter_entity(hass, entry, "sensor", "next_action"))
    plain = datetime.fromisoformat(next_action.state)
    assert next_action.attributes["phase"] == "dusk"
    assert "shift_morning" not in trace(hass, entry, "schedule")["values"]

    coordinator = entry.runtime_data
    coordinator.shift_seed = 4242
    subentry = next(iter(entry.subentries))
    expected = RandomShift(4242, subentry, 30)
    day = date(2026, 11, 18)

    await set_holiday(hass, entry, True)
    values = trace(hass, entry, "schedule")["values"]
    assert values["shift_morning"] == expected.morning(day) and values["shift_evening"] == expected.evening(
        day
    )
    assert -30 <= values["shift_morning"] <= 30 and -30 <= values["shift_evening"] <= 30
    shifted = datetime.fromisoformat(
        hass.states.get(shutter_entity(hass, entry, "sensor", "next_action")).state
    )
    assert shifted - plain == timedelta(minutes=expected.evening(day))

    await set_holiday(hass, entry, False)
    assert "shift_morning" not in trace(hass, entry, "schedule")["values"]
    unshifted = hass.states.get(shutter_entity(hass, entry, "sensor", "next_action")).state
    assert datetime.fromisoformat(unshifted) == plain


async def test_the_shift_follows_the_option(hass: HomeAssistant, covers, noon) -> None:
    entry = await setup(hass, presence=None, holiday_shift=0)
    mock_moves(hass)
    await add_shutter(hass, entry, LIVING)
    await set_holiday(hass, entry, True)
    values = trace(hass, entry, "schedule")["values"]
    assert values["shift_morning"] == 0 and values["shift_evening"] == 0


async def test_a_restart_keeps_holiday_and_the_shifts(hass: HomeAssistant, covers, noon) -> None:
    entry = await setup(hass, presence=None)
    mock_moves(hass)
    await add_shutter(hass, entry, LIVING)
    await set_holiday(hass, entry, True)
    seed = entry.runtime_data.shift_seed
    values = trace(hass, entry, "schedule")["values"]
    next_action = hass.states.get(shutter_entity(hass, entry, "sensor", "next_action")).state

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert holiday(hass, entry).state == "on" and away(hass, entry).state == "on"
    assert entry.runtime_data.shift_seed == seed != 0
    assert trace(hass, entry, "schedule")["values"] == values
    assert hass.states.get(shutter_entity(hass, entry, "sensor", "next_action")).state == next_action


async def test_diagnostics_have_away_and_holiday_but_not_the_presence_entity(
    hass: HomeAssistant, covers, noon
) -> None:
    hass.states.async_set(PRESENCE, "on")
    entry = await setup(hass)
    mock_moves(hass)
    await add_shutter(hass, entry, LIVING)
    await set_holiday(hass, entry, True)

    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["base"]["away"] is True and result["base"]["holiday"] is True
    assert PRESENCE not in json.dumps(result)
