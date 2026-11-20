"""What the card needs from the integration: language, next actions, moving, and serving the card (#9)."""

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from custom_components.smart_shutter_control import async_register_card

from .conftest import LIVING, add_shutter, setup_base
from .test_schedule import amsterdam, eid, report  # noqa: F401  (fixture)


async def test_language_names_the_entities(hass: HomeAssistant, covers) -> None:
    report(hass, 100)
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    reason = hass.states.get(eid(hass, entry, "sensor", "reason"))
    assert reason.attributes["language"] is None
    assert reason.name.endswith("Reason")

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "language"}
    )
    assert result["type"] is FlowResultType.FORM
    await hass.config_entries.options.async_configure(result["flow_id"], {"language": "nl"})
    await hass.async_block_till_done()
    reason = hass.states.get(eid(hass, entry, "sensor", "reason"))
    assert reason.attributes["language"] == "nl"
    assert reason.name.endswith("Reden")
    assert hass.states.get(eid(hass, entry, "switch", "sleep_in")).name.endswith("Uitslapen")


async def test_following_changes_and_moving(hass: HomeAssistant, covers, amsterdam) -> None:  # noqa: F811
    amsterdam.move_to("2026-11-18 12:00:00+01:00")
    report(hass, 100)
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    next_action = hass.states.get(eid(hass, entry, "sensor", "next_action"))
    assert next_action.attributes["phase"] == "dusk"
    following = next_action.attributes["following"]
    assert [f["phase"] for f in following] == ["night", "slit"]
    assert following[0]["position"] == 0 and following[1]["position"] == "slit"
    cover = eid(hass, entry, "cover", "shutter")
    hass.states.async_set(LIVING, "closing", {"current_position": 80, "supported_features": 15})
    await hass.async_block_till_done()
    assert hass.states.get(cover).state == "closing"


async def test_card_is_served(hass: HomeAssistant) -> None:
    assert not await async_register_card(hass)  # no http in this test: skipped quietly
    assert await async_setup_component(hass, "smart_shutter_control", {})
