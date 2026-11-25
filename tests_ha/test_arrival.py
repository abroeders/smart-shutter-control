"""Arrival checks retry one move and report shutters that never arrive."""

import time

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.smart_shutter_control.core.model import Decision
from custom_components.smart_shutter_control.core.rules import RuleChain

from .conftest import LIVING, add_shutter, position_of, register_moves, setup_base


class FixedRule:
    def __init__(self, position: int) -> None:
        self.position = position
        self.priority = 10

    def propose(self, ctx):
        return Decision(self.position, "manual")


def entity(hass: HomeAssistant, entry, key: str) -> str:
    subentry_id = next(iter(entry.subentries))
    return er.async_get(hass).async_get_entity_id(
        "binary_sensor", "smart_shutter_control", f"{entry.entry_id}_{subentry_id}_{key}"
    )


async def prepare(hass: HomeAssistant) -> tuple:
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    subentry_id = next(iter(entry.subentries))
    controller = entry.runtime_data.shutters[subentry_id]
    controller.chain = RuleChain([FixedRule(50)])
    controller.last_target = None
    return entry, subentry_id, controller


async def test_first_ignore_then_second_arrives(hass: HomeAssistant, covers, freezer) -> None:
    freezer.move_to("2026-11-21 20:00:00+00:00")
    entry, subentry_id, controller = await prepare(hass)
    moves: list[int] = []

    async def move(call: ServiceCall) -> None:
        target = position_of(call)
        moves.append(target)
        if len(moves) == 2:
            hass.states.async_set(LIVING, "open", {"current_position": target, "supported_features": 15})

    register_moves(hass, move)
    await entry.runtime_data.async_tick()
    assert moves == [50]

    freezer.move_to("2026-11-21 20:03:01+00:00")
    await entry.runtime_data.async_tick()
    await hass.async_block_till_done()
    assert moves == [50, 50]
    assert not controller.stuck
    issue = ir.async_get(hass).async_get_issue("smart_shutter_control", f"stuck_{subentry_id}")
    assert issue is None


async def test_never_moves_creates_issue_then_later_move_clears_it(
    hass: HomeAssistant, covers, freezer
) -> None:
    freezer.move_to("2026-11-21 20:00:00+00:00")
    entry, subentry_id, controller = await prepare(hass)
    moves: list[int] = []
    arrived = False

    async def move(call: ServiceCall) -> None:
        moves.append(position_of(call))
        if arrived:
            hass.states.async_set(
                LIVING, "open", {"current_position": position_of(call), "supported_features": 15}
            )

    register_moves(hass, move)
    await entry.runtime_data.async_tick()
    assert moves == [50]

    freezer.move_to("2026-11-21 20:03:01+00:00")
    await entry.runtime_data.async_tick()
    assert moves == [50, 50]

    freezer.move_to("2026-11-21 20:06:02+00:00")
    await entry.runtime_data.async_tick()
    await hass.async_block_till_done()

    stuck = entity(hass, entry, "stuck")
    assert hass.states.get(stuck).state == "on"
    assert hass.states.get(stuck).attributes["target"] == 50
    assert hass.states.get(stuck).attributes["position"] == 100
    assert ir.async_get(hass).async_get_issue("smart_shutter_control", f"stuck_{subentry_id}") is not None

    arrived = True
    controller.last_target = None
    freezer.move_to("2026-11-21 20:09:03+00:00")
    await entry.runtime_data.async_tick()
    await hass.async_block_till_done()
    freezer.move_to("2026-11-21 20:12:04+00:00")
    await entry.runtime_data.async_tick()
    await hass.async_block_till_done()
    assert hass.states.get(stuck).state == "off"
    assert ir.async_get(hass).async_get_issue("smart_shutter_control", f"stuck_{subentry_id}") is None


async def test_manual_report_cancels_arrival_check(hass: HomeAssistant, covers, freezer) -> None:
    freezer.move_to("2026-11-21 20:00:00+00:00")
    entry, subentry_id, controller = await prepare(hass)
    moves: list[int] = []

    async def move(call: ServiceCall) -> None:
        moves.append(position_of(call))

    register_moves(hass, move)
    await entry.runtime_data.async_tick()
    assert moves == [50]
    controller.chain = RuleChain([])

    hass.states.async_set(LIVING, "open", {"current_position": 30, "supported_features": 15})
    await hass.async_block_till_done()
    assert not controller.arrival.active
    assert moves == [50]
    freezer.move_to("2026-11-21 20:03:01+00:00")
    await entry.runtime_data.async_tick()
    await hass.async_block_till_done()

    assert moves == [50]
    assert not controller.arrival.active
    assert not controller.stuck


async def test_reversal_during_the_move_pauses_and_is_not_retried(
    hass: HomeAssistant, covers, freezer
) -> None:
    """#108: the user presses up while the controller moves the shutter down."""
    freezer.move_to("2026-11-21 20:00:00+00:00")
    entry, _subentry_id, controller = await prepare(hass)
    moves: list[int] = []

    async def move(call: ServiceCall) -> None:
        moves.append(position_of(call))

    register_moves(hass, move)
    await entry.runtime_data.async_tick()
    assert moves == [50]
    controller.chain = RuleChain([])  # only a retry of the arrival check could move it now
    for position in (70, 60, 66):  # on its way down, then back up
        hass.states.async_set(LIVING, "open", {"current_position": position, "supported_features": 15})
        await hass.async_block_till_done()
    assert controller.pause.on and not controller.arrival.active

    freezer.move_to("2026-11-21 20:03:01+00:00")
    await entry.runtime_data.async_tick()
    await hass.async_block_till_done()
    assert moves == [50]
    assert not controller.stuck


async def test_stop_halfway_with_a_power_sensor_pauses(hass: HomeAssistant, covers, freezer) -> None:
    """#108: the motor stops short of the target and the module stays there."""
    freezer.move_to("2026-11-21 20:00:00+00:00")
    entry, _subentry_id, controller = await prepare(hass)
    power = "sensor.living_power"
    hass.states.async_set(power, "0", {"device_class": "power", "unit_of_measurement": "W"})
    controller.adapter.power_entity = power
    controller.observe()
    moves: list[int] = []

    async def move(call: ServiceCall) -> None:
        moves.append(position_of(call))

    register_moves(hass, move)
    await entry.runtime_data.async_tick()
    assert moves == [50]
    hass.states.async_set(power, "120", {"device_class": "power", "unit_of_measurement": "W"})
    hass.states.async_set(LIVING, "open", {"current_position": 70, "supported_features": 15})
    controller.observe()
    freezer.move_to("2026-11-21 20:00:20+00:00")
    hass.states.async_set(power, "0", {"device_class": "power", "unit_of_measurement": "W"})
    controller.observe()
    assert not controller.pause.on

    await controller.async_check_arrival()  # due, but a late report may still come
    assert not controller.pause.on and controller.arrival.active
    entry.runtime_data._check_arrival_later(controller.detector.settling(time.time()))
    freezer.tick(6)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert controller.pause.on and not controller.arrival.active
    assert moves == [50]
