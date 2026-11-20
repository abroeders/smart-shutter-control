"""The calibration assistant with a simulated shutter, and the calibrated shutter entity afterwards."""

import pytest
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er

from custom_components.smart_shutter_control import assistant

from .conftest import LIVING, add_shutter, setup_base

# real opening (%) per module position (%) per direction, like a roller that is slower going up
UP = {25: 9, 50: 27, 75: 54}
DOWN = {75: 60, 50: 31, 25: 11}


@pytest.fixture
def fast(monkeypatch):
    monkeypatch.setattr(assistant, "POLL", 0.01)
    monkeypatch.setattr(assistant, "STABLE", 0.0)
    monkeypatch.setattr(assistant, "MAX_WAIT", 2.0)


def physical(hass: HomeAssistant) -> list[int]:
    """The physical cover goes straight to the requested position."""
    moves: list[int] = []

    async def set_position(call: ServiceCall) -> None:
        position = int(call.data["position"])
        moves.append(position)
        hass.states.async_set(
            LIVING,
            "open" if position else "closed",
            {"current_position": position, "supported_features": 15, "friendly_name": "Living room"},
        )

    hass.services.async_register("cover", "set_cover_position", set_position)
    return moves


async def run(hass: HomeAssistant, flow_id: str, result):
    """Let progress steps finish."""
    while result["type"] in (FlowResultType.SHOW_PROGRESS, FlowResultType.SHOW_PROGRESS_DONE):
        await hass.async_block_till_done()
        result = await hass.config_entries.subentries.async_configure(flow_id)
    return result


async def open_menu(hass: HomeAssistant, entry, subentry_id: str, choice: str):
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"), context={"source": "reconfigure", "subentry_id": subentry_id}
    )
    return await hass.config_entries.subentries.async_configure(result["flow_id"], {"next_step_id": choice})


async def test_full_calibration(hass: HomeAssistant, covers, fast) -> None:
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    moves = physical(hass)
    subentry_id = next(iter(entry.subentries))
    controller = entry.runtime_data.shutters[subentry_id]

    result = await open_menu(hass, entry, subentry_id, "calibrate")
    assert result["step_id"] == "calibrate"
    flow_id = result["flow_id"]
    result = await run(
        hass,
        flow_id,
        await hass.config_entries.subentries.async_configure(flow_id, {"window_height_cm": 140}),
    )
    assert controller.paused
    while result["step_id"] == "cal_measure":
        module = int(result["description_placeholders"]["position"])
        table = UP if result["description_placeholders"]["direction"] == "↑" else DOWN
        cm = table[module] / 100 * 140
        result = await run(
            hass, flow_id, await hass.config_entries.subentries.async_configure(flow_id, {"opening": cm})
        )
    while result["step_id"] == "cal_lift":  # the bar lifts at 6 %
        lifted = int(result["description_placeholders"]["position"]) >= 6
        result = await run(
            hass, flow_id, await hass.config_entries.subentries.async_configure(flow_id, {"lifted": lifted})
        )
    assert result["step_id"] == "cal_review"
    assert "↑" in result["description_placeholders"]["summary"]
    result = await hass.config_entries.subentries.async_configure(flow_id, {})
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()

    assert moves[:4] == [0, 25, 50, 75] and 100 in moves
    data = entry.subentries[subentry_id].data["calibration"]
    assert len(data["points"]["up"]) == 3 and len(data["points"]["down"]) == 3
    assert data["slit"]["up"] == pytest.approx(0.04)

    controller = entry.runtime_data.shutters[subentry_id]  # reloaded
    assert controller.calibration.calibrated and not controller.paused
    registry = er.async_get(hass)
    sensor = registry.async_get_entity_id(
        "sensor", "smart_shutter_control", f"{entry.entry_id}_{subentry_id}_calibration"
    )
    assert hass.states.get(sensor).state == "calibrated"
    cover = registry.async_get_entity_id(
        "cover", "smart_shutter_control", f"{entry.entry_id}_{subentry_id}_shutter"
    )
    attrs = hass.states.get(cover).attributes
    assert attrs["calibrated"] is True and "slit" in attrs
    assert controller.calibration.slit(controller.direction().UP) == 4

    # a real 50 % from closed and from open needs different module positions
    up = controller.calibration.to_module(50, controller.direction().UP)
    down = controller.calibration.to_module(50, controller.direction().DOWN)
    assert up > 50 and down > 50 and up != down


async def test_cancel_resumes_automatic_control(hass: HomeAssistant, covers, fast) -> None:
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    physical(hass)
    subentry_id = next(iter(entry.subentries))
    controller = entry.runtime_data.shutters[subentry_id]
    result = await open_menu(hass, entry, subentry_id, "calibrate")
    flow_id = result["flow_id"]
    await run(hass, flow_id, await hass.config_entries.subentries.async_configure(flow_id, {}))
    assert controller.paused
    hass.config_entries.subentries.async_abort(flow_id)
    assert not controller.paused


async def test_add_one_point(hass: HomeAssistant, covers, fast) -> None:
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    moves = physical(hass)
    subentry_id = next(iter(entry.subentries))
    result = await open_menu(hass, entry, subentry_id, "add_point")
    flow_id = result["flow_id"]
    result = await run(
        hass,
        flow_id,
        await hass.config_entries.subentries.async_configure(flow_id, {"module": 40, "direction": "down"}),
    )
    assert result["step_id"] == "cal_measure" and moves == [40]  # already open: straight down to 40
    result = await hass.config_entries.subentries.async_configure(
        flow_id, {"opening": 22}
    )  # % without a height
    assert result["step_id"] == "cal_review"
    result = await hass.config_entries.subentries.async_configure(flow_id, {})
    await hass.async_block_till_done()
    assert entry.subentries[subentry_id].data["calibration"]["points"]["down"] == [[0.4, 0.22]]
