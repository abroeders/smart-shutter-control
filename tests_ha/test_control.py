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


async def test_schedule_leaves_an_open_shutter_by_day(hass: HomeAssistant, covers, freezer) -> None:
    freezer.move_to("2026-11-18 12:00:00+01:00")  # a Wednesday at noon: the day phase wants it open
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    entry = await setup_base(hass)
    calls = async_mock_service(hass, "cover", "set_cover_position")
    await add_shutter(hass, entry, LIVING)
    await entry.runtime_data.async_tick()
    assert not calls  # already open
    assert hass.states.get(entity(hass, entry, "sensor", "reason")).state == "schedule"
    assert hass.states.get(entity(hass, entry, "sensor", "phase")).state == "day"


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


async def test_opening_number_moves_to_the_real_position(hass: HomeAssistant, covers) -> None:
    from custom_components.smart_shutter_control.core.calibration import RollerCalibration

    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    controller = next(iter(entry.runtime_data.shutters.values()))
    controller.calibration = RollerCalibration.from_data(
        {
            "points": {"up": [[0.5, 0.25], [0.75, 0.58]], "down": [[0.5, 0.25], [0.75, 0.58]]},
            "slit": {"up": 0.2},
        }
    )
    calls = async_mock_service(hass, "cover", "set_cover_position")
    number = entity(hass, entry, "number", "opening")
    await hass.services.async_call("number", "set_value", {"entity_id": number, "value": 50}, blocking=True)
    module = calls[-1].data["position"]
    assert module > 50  # half open needs more than half the travel time
    # one module percent is about two real percents here: the closest whole position is within 1 %
    assert abs(controller.calibration.from_module(module, controller.direction()) - 50) <= 1

    # fully open and fully closed are the module's own end positions (limit switches)
    await hass.services.async_call("number", "set_value", {"entity_id": number, "value": 100}, blocking=True)
    assert calls[-1].data["position"] == 100
    await hass.services.async_call("number", "set_value", {"entity_id": number, "value": 0}, blocking=True)
    assert calls[-1].data["position"] == 0

    # in the slit the opening is 0 %, but the shutter is not closed
    hass.states.async_set(LIVING, "open", {"current_position": 18, "supported_features": 15})
    await hass.async_block_till_done()
    entry.runtime_data.async_update_listeners()
    await hass.async_block_till_done()
    assert float(hass.states.get(number).state) == 0
    assert hass.states.get(entity(hass, entry, "cover", "shutter")).state == "open"
    assert hass.states.get(entity(hass, entry, "sensor", "stand")).state == "slit"


async def test_motor_power_sensor_is_found_on_the_device(hass: HomeAssistant, covers) -> None:
    from homeassistant.helpers import device_registry as dr
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.smart_shutter_control.adapter import CoverAdapter

    other = MockConfigEntry(domain="zwave_js")
    other.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=other.entry_id, identifiers={("zwave_js", "8")}
    )
    registry = er.async_get(hass)
    registry.async_get_or_create("cover", "zwave_js", "c8", device_id=device.id, suggested_object_id="living")
    for uid, object_id, value in (("p1", "stale_w", "672"), ("p2", "consumption_w", "0.0")):
        registry.async_get_or_create(
            "sensor",
            "zwave_js",
            uid,
            device_id=device.id,
            suggested_object_id=object_id,
            original_device_class="power",
        )
        hass.states.async_set(f"sensor.{object_id}", value, {"unit_of_measurement": "W"})
    assert CoverAdapter(hass, "cover.living").power_entity == "sensor.consumption_w"  # not the stale 672 W
    assert CoverAdapter(hass, "cover.unknown").power_entity is None
