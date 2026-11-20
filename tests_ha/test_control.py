"""The controller moves only when automatic control is on, never above the maximum; the cover forwards."""

from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.smart_shutter_control.core.model import Decision
from custom_components.smart_shutter_control.core.rules import RuleChain

from .conftest import LIVING, add_shutter, setup_base


@dataclass
class FixedRule:
    position: int
    priority: int = 10

    def propose(self, ctx):
        return Decision(self.position, "manual")


def entity(hass: HomeAssistant, entry, domain: str, key: str) -> str:
    subentry_id = next(iter(entry.subentries))
    return er.async_get(hass).async_get_entity_id(
        domain, "smart_shutter_control", f"{entry.entry_id}_{subentry_id}_{key}"
    )


async def test_no_rules_means_idle_and_no_move(hass: HomeAssistant, covers) -> None:
    entry = await setup_base(hass)
    calls = async_mock_service(hass, "cover", "set_cover_position")
    await add_shutter(hass, entry, LIVING)
    await entry.runtime_data.async_tick()
    assert not calls
    assert hass.states.get(entity(hass, entry, "sensor", "reason")).state == "idle"


async def test_moves_limited_and_only_when_automatic(hass: HomeAssistant, covers) -> None:
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING, max_position=60)
    calls = async_mock_service(hass, "cover", "set_cover_position")
    controller = next(iter(entry.runtime_data.shutters.values()))
    controller.chain = RuleChain([FixedRule(90)])
    await entry.runtime_data.async_tick()
    assert calls[-1].data == {"entity_id": LIVING, "position": 60}  # limited to the maximum position
    assert controller.adapter.last_command.automatic

    calls.clear()
    switch = entity(hass, entry, "switch", "automatic")
    await hass.services.async_call("switch", "turn_off", {"entity_id": switch}, blocking=True)
    assert not calls
    assert hass.states.get(entity(hass, entry, "sensor", "reason")).state == "off"

    number = entity(hass, entry, "number", "max_position")
    await hass.services.async_call("number", "set_value", {"entity_id": number, "value": 40}, blocking=True)
    assert float(hass.states.get(number).state) == 40


async def test_cover_entity_forwards_without_limits(hass: HomeAssistant, covers) -> None:
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING, max_position=50)
    calls = async_mock_service(hass, "cover", "set_cover_position")
    cover_id = entity(hass, entry, "cover", "shutter")
    assert hass.states.get(cover_id).attributes["current_position"] == 100
    # the mocked cover service would also catch calls to our own cover entity: call the entity directly
    cover = hass.data["entity_components"]["cover"].get_entity(cover_id)
    await cover.async_set_cover_position(position=80)
    assert calls[-1].data == {"entity_id": LIVING, "position": 80}  # by hand above the maximum is allowed
    controller = next(iter(entry.runtime_data.shutters.values()))
    assert controller.adapter.last_command.automatic is False
    await cover.async_close_cover()
    assert calls[-1].data["position"] == 0
