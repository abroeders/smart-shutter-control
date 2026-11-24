"""The diagnostics file: sections, values of the entities, redaction."""

import json

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.smart_shutter_control.const import DOMAIN
from custom_components.smart_shutter_control.diagnostics import (
    REDACTED,
    async_get_config_entry_diagnostics,
)

from .conftest import BEDROOM, LIVING, add_shutter, setup_base


def state_of(hass: HomeAssistant, entry, subentry_id: str, domain: str, key: str):
    unique = f"{entry.entry_id}_{subentry_id}_{key}"
    return hass.states.get(er.async_get(hass).async_get_entity_id(domain, DOMAIN, unique))


async def test_sections_and_values_of_the_entities(hass: HomeAssistant, covers) -> None:
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    await add_shutter(hass, entry, BEDROOM)
    result = await async_get_config_entry_diagnostics(hass, entry)

    assert set(result) == {"integration", "entry", "base", "shutters"}
    assert {"version", "home_assistant", "unit_system", "time_zone"} <= set(result["integration"])
    assert {"paused", "sun", "weather", "clear_sky_reference"} <= set(result["base"])
    assert [s["cover"] for s in result["shutters"]] == [LIVING, BEDROOM]
    for shutter in result["shutters"]:
        assert {"title", "subentry_id", "data", "state", "decision", "next_action", "position_memory"} <= set(
            shutter
        )
        reason = state_of(hass, entry, shutter["subentry_id"], "sensor", "reason")
        phase = state_of(hass, entry, shutter["subentry_id"], "sensor", "phase")
        assert shutter["state"]["reason"] == reason.state
        assert shutter["state"]["phase"] == phase.state
        assert shutter["decision"] == reason.attributes["decision"]
        assert shutter["state"]["calibrated"] is False


async def test_location_and_people_are_redacted(hass: HomeAssistant, covers) -> None:
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    subentry = next(iter(entry.subentries.values()))
    hass.config_entries.async_update_subentry(
        entry, subentry, data={**subentry.data, "owner": "person.resident"}
    )
    hass.config_entries.async_update_entry(
        entry, data={**entry.data, "latitude": 52.0, "longitude": 5.0, "location_name": "Home"}
    )
    await hass.async_block_till_done()
    result = await async_get_config_entry_diagnostics(hass, entry)

    assert {
        k: result["entry"]["data"][k] for k in ("latitude", "longitude", "location_name")
    } == dict.fromkeys(("latitude", "longitude", "location_name"), REDACTED)
    assert result["shutters"][0]["data"]["owner"] == REDACTED
    assert result["shutters"][0]["cover"] == LIVING


async def test_without_shutters(hass: HomeAssistant, covers) -> None:
    entry = await setup_base(hass)
    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["shutters"] == []


async def test_json_serialisable(hass: HomeAssistant, covers) -> None:
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    await add_shutter(hass, entry, BEDROOM)

    json.dumps(await async_get_config_entry_diagnostics(hass, entry))
