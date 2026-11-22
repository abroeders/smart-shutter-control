"""The calibration assistant with a simulated shutter, and the calibrated shutter entity afterwards."""

import asyncio

import pytest
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

from custom_components.smart_shutter_control import assistant

from .conftest import LIVING, add_shutter, position_of, register_moves, setup_base

# real opening (%) for a module position (%): the bar leaves the sill at 6 %, a bit lower going up


def opening(module: int, direction: str) -> float:
    lift = 6
    if module <= lift:
        return 0.0
    share = (module - lift) / (100 - lift)
    return 100 * share * (0.55 + 0.45 * share) * (0.97 if direction == "↑" else 1.0)


@pytest.fixture
def fast(monkeypatch):
    monkeypatch.setattr(assistant, "POLL", 0.01)
    monkeypatch.setattr(assistant, "STABLE", 0.03)
    monkeypatch.setattr(assistant, "START_WAIT", 0.1)
    monkeypatch.setattr(assistant, "IDLE", 0.03)
    monkeypatch.setattr(assistant, "REPORT_WAIT", 1.0)
    monkeypatch.setattr(assistant, "END_SETTLE", 0.0)
    monkeypatch.setattr(assistant, "END_STABLE_NO_POWER", 0.05)
    monkeypatch.setattr(assistant, "END_SETTLE_NO_POWER", 0.0)
    monkeypatch.setattr(assistant, "TRAVEL_MARGIN", 0.05)
    monkeypatch.setattr(assistant, "MAX_WAIT", 2.0)


def physical(hass: HomeAssistant, stop_short: dict[int, int] | None = None) -> list[int]:
    """The physical cover goes straight to the requested position (or stops short once, like a module
    that gets a command while it still runs on to its limit switch)."""
    moves: list[int] = []
    short = dict(stop_short or {})

    async def set_position(call: ServiceCall) -> None:
        position = position_of(call)
        moves.append(position)
        position = short.pop(position, position)
        hass.states.async_set(
            LIVING,
            "open" if position else "closed",
            {"current_position": position, "supported_features": 15, "friendly_name": "Living room"},
        )

    register_moves(hass, set_position)
    return moves


async def run(hass: HomeAssistant, flow_id: str, result):
    """Let progress steps finish."""
    while result["type"] in (FlowResultType.SHOW_PROGRESS, FlowResultType.SHOW_PROGRESS_DONE):
        await hass.async_block_till_done()
        result = await hass.config_entries.subentries.async_configure(flow_id)
    return result


async def open_menu(hass: HomeAssistant, entry, subentry_id: str, choice: str):
    """Open the shutter's menu and choose; "calibrate" goes on to the assistant (its own menu, #40)."""
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"), context={"source": "reconfigure", "subentry_id": subentry_id}
    )
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {"next_step_id": choice})
    if choice == "calibrate":
        assert result["type"] is FlowResultType.MENU
        assert result["menu_options"] == ["cal_assistant", "cal_table"]
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"], {"next_step_id": "cal_assistant"}
        )
    return result


async def test_full_calibration(hass: HomeAssistant, covers, fast) -> None:
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    moves = physical(hass)
    subentry_id = next(iter(entry.subentries))
    controller = entry.runtime_data.shutters[subentry_id]

    result = await open_menu(hass, entry, subentry_id, "calibrate")
    assert result["step_id"] == "cal_assistant"
    flow_id = result["flow_id"]
    result = await run(
        hass,
        flow_id,
        await hass.config_entries.subentries.async_configure(flow_id, {"window_height_cm": 140}),
    )
    assert controller.paused
    assert result["step_id"] == "cal_lift"  # first the lift point
    while result["step_id"] == "cal_lift":  # the bar lifts at 6 %
        lifted = int(result["description_placeholders"]["position"]) >= 6
        result = await run(
            hass, flow_id, await hass.config_entries.subentries.async_configure(flow_id, {"lifted": lifted})
        )
    measured = []
    while result["step_id"] == "cal_measure":
        module = int(result["description_placeholders"]["position"])
        direction = result["description_placeholders"]["direction"]
        measured.append((module, direction))
        cm = opening(module, direction) / 100 * 140
        result = await run(
            hass, flow_id, await hass.config_entries.subentries.async_configure(flow_id, {"opening": cm})
        )
    assert measured == [
        (20, "↑"),
        (44, "↑"),
        (67, "↑"),
        (91, "↑"),
        (91, "↓"),
        (67, "↓"),
        (44, "↓"),
        (20, "↓"),
    ]
    assert result["step_id"] == "cal_review"
    assert "↑" in result["description_placeholders"]["summary"]
    result = await hass.config_entries.subentries.async_configure(flow_id, {})
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()

    assert moves[:5] == [0, 2, 4, 6, 20] and 100 in moves
    data = entry.subentries[subentry_id].data["calibration"]
    assert len(data["points"]["up"]) == 4 and len(data["points"]["down"]) == 4
    assert all(o > 0 for _, o in data["points"]["up"] + data["points"]["down"])  # none on the sill
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


async def test_us_customary_calibration_uses_inches(hass: HomeAssistant, covers, fast) -> None:
    hass.config.units = US_CUSTOMARY_SYSTEM
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    physical(hass)
    subentry_id = next(iter(entry.subentries))

    result = await open_menu(hass, entry, subentry_id, "calibrate")
    assert result["step_id"] == "cal_assistant"

    flow_id = result["flow_id"]
    result = await run(
        hass,
        flow_id,
        await hass.config_entries.subentries.async_configure(flow_id, {"window_height_cm": 60}),
    )
    session = controller_flow_session(hass, flow_id)
    assert session.height_cm == pytest.approx(152.4)

    while result["step_id"] == "cal_lift":
        lifted = int(result["description_placeholders"]["position"]) >= 6
        result = await run(
            hass, flow_id, await hass.config_entries.subentries.async_configure(flow_id, {"lifted": lifted})
        )
    while result["step_id"] == "cal_measure":
        opening_field = next(k for k in result["data_schema"].schema if str(k) == "opening")
        assert result["data_schema"].schema[opening_field].config["unit_of_measurement"] == "in"
        assert result["data_schema"].schema[opening_field].config["step"] == 0.25
        result = await run(
            hass,
            flow_id,
            await hass.config_entries.subentries.async_configure(flow_id, {"opening": 30}),
        )
    assert result["step_id"] == "cal_review"
    assert any(pytest.approx(0.5) == opening for _, opening in session.points["up"] + session.points["down"])


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


async def test_a_shutter_that_stops_short_gets_the_command_again(hass: HomeAssistant, covers, fast) -> None:
    hass.states.async_set(LIVING, "closed", {"current_position": 0, "supported_features": 15})
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    moves = physical(hass, stop_short={25: 13})  # the first move to 25 ends at 13
    subentry_id = next(iter(entry.subentries))
    result = await open_menu(hass, entry, subentry_id, "add_point")
    flow_id = result["flow_id"]
    result = await run(
        hass,
        flow_id,
        await hass.config_entries.subentries.async_configure(flow_id, {"module": 25, "direction": "up"}),
    )
    assert result["step_id"] == "cal_measure"
    assert result["description_placeholders"]["reached"] == "✓"
    assert moves == [25, 25]  # sent again after it stopped at 13
    assert hass.states.get(LIVING).attributes["current_position"] == 25


def test_a_point_on_the_sill_adds_one_higher_and_skips_lower_ones() -> None:
    from types import SimpleNamespace

    from custom_components.smart_shutter_control.assistant import Action, CalibrationSession
    from custom_components.smart_shutter_control.core.model import Direction

    session = CalibrationSession(SimpleNamespace())
    session.plan_measuring(20)
    assert session.measuring == [32, 52, 72, 92]
    up = session.queue.pop(0)
    session.add_point(up, 0)  # the bar is still on the sill at 32
    assert session.queue[0] == Action("measure", 42, Direction.UP)
    session.queue = [Action("measure", 32, Direction.DOWN)]  # 72 and 52 done; going down
    session.add_point(Action("measure", 52, Direction.DOWN), 0)  # already on the sill at 52
    assert session.queue == []  # so 32 is skipped


POWER = "sensor.living_room_motor_power"


def travelling(hass: HomeAssistant, seconds: float = 0.3, report_delay: float = 0.0) -> list[int]:
    """A cover that takes a while to travel and reports its position only now and then, with motor power."""
    moves: list[int] = []
    hass.states.async_set(POWER, "0", {"device_class": "power", "unit_of_measurement": "W"})

    async def set_position(call: ServiceCall) -> None:
        target = position_of(call)
        moves.append(target)
        start = hass.states.get(LIVING).attributes["current_position"]

        async def run() -> None:
            hass.states.async_set(POWER, "100", {"device_class": "power", "unit_of_measurement": "W"})
            await asyncio.sleep(seconds / 2)
            middle = (start + target) // 2  # one report half way, then silence
            hass.states.async_set(LIVING, "open", {"current_position": middle, "supported_features": 15})
            await asyncio.sleep(seconds / 2)
            hass.states.async_set(
                LIVING,
                "closed" if target == 0 else "open",
                {"current_position": target, "supported_features": 15},
            )
            hass.states.async_set(POWER, "0", {"device_class": "power", "unit_of_measurement": "W"})

        hass.async_create_task(run())

    register_moves(hass, set_position)
    return moves


async def test_closing_is_one_command_and_waits_for_the_end(hass: HomeAssistant, covers, fast) -> None:
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING, motor_power=POWER)
    moves = travelling(hass)
    subentry_id = next(iter(entry.subentries))
    result = await open_menu(hass, entry, subentry_id, "calibrate")
    flow_id = result["flow_id"]
    result = await run(hass, flow_id, await hass.config_entries.subentries.async_configure(flow_id, {}))
    # the first lift step only after the shutter really reached 0 (one command, no steps on the way)
    assert result["step_id"] == "cal_lift"
    assert moves == [0, 2]
    assert hass.states.get(LIVING).attributes["current_position"] == 2


async def test_intermediate_points_wait_for_the_late_report(hass: HomeAssistant, covers, fast) -> None:
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING, motor_power=POWER)
    moves = travelling(hass, report_delay=0.2)  # the final position comes well after the motor stopped
    subentry_id = next(iter(entry.subentries))
    result = await open_menu(hass, entry, subentry_id, "add_point")
    flow_id = result["flow_id"]
    result = await run(
        hass,
        flow_id,
        await hass.config_entries.subentries.async_configure(flow_id, {"module": 40, "direction": "down"}),
    )
    assert result["step_id"] == "cal_measure"
    assert result["description_placeholders"]["reached"] == "✓"
    assert moves == [40]  # one command: no stop-and-go while the report was on its way


async def test_a_report_on_the_way_up_is_not_taken_for_the_next_point(
    hass: HomeAssistant, covers, fast
) -> None:
    hass.states.async_set(LIVING, "open", {"current_position": 84, "supported_features": 15})
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING, motor_power=POWER)
    moves = travelling(hass)  # on the way from 84 to 100 it reports 92 half way
    subentry_id = next(iter(entry.subentries))
    result = await open_menu(hass, entry, subentry_id, "add_point")
    flow_id = result["flow_id"]
    result = await run(
        hass,
        flow_id,
        await hass.config_entries.subentries.async_configure(flow_id, {"module": 92, "direction": "down"}),
    )
    assert result["step_id"] == "cal_measure"
    assert moves == [100, 92]  # first really at 100, then down to 92 before asking for the opening
    assert hass.states.get(LIVING).attributes["current_position"] == 92


def silent(hass: HomeAssistant, travel: float = 0.4) -> list[int]:
    """A shutter without a power sensor that reports only when it arrives, after a travel time."""
    moves: list[int] = []

    async def set_position(call: ServiceCall) -> None:
        target = position_of(call)
        moves.append(target)
        start = hass.states.get(LIVING).attributes["current_position"]

        async def run() -> None:
            await asyncio.sleep(abs(target - start) / 100 * travel)
            hass.states.async_set(
                LIVING,
                "closed" if target == 0 else "open",
                {"current_position": target, "supported_features": 15},
            )

        hass.async_create_task(run())

    register_moves(hass, set_position)
    return moves


async def test_without_power_sensor_the_travel_time_is_measured(hass: HomeAssistant, covers, fast) -> None:
    hass.states.async_set(LIVING, "open", {"current_position": 50, "supported_features": 15})
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    moves = silent(hass)
    subentry_id = next(iter(entry.subentries))
    controller = entry.runtime_data.shutters[subentry_id]
    assert controller.adapter.power_entity is None
    result = await open_menu(hass, entry, subentry_id, "calibrate")
    flow_id = result["flow_id"]
    result = await run(hass, flow_id, await hass.config_entries.subentries.async_configure(flow_id, {}))
    assert result["step_id"] == "cal_lift"
    assert moves[:3] == [100, 0, 2]  # open, time the travel to closed, then the first lift step
    session = controller_flow_session(hass, flow_id)
    assert 0.3 <= session.travel_time <= 1.5  # the simulated full travel takes 0.4 s (plus polling)
    while result["step_id"] == "cal_lift":
        lifted = int(result["description_placeholders"]["position"]) >= 4
        result = await run(
            hass, flow_id, await hass.config_entries.subentries.async_configure(flow_id, {"lifted": lifted})
        )
    first = int(result["description_placeholders"]["position"])
    assert (
        result["step_id"] == "cal_measure" and moves.count(first) == 1
    )  # one command, waited for the arrival
    assert hass.states.get(LIVING).attributes["current_position"] == first


def controller_flow_session(hass: HomeAssistant, flow_id: str):
    flow = hass.config_entries.subentries._progress[flow_id]  # noqa: SLF001
    return flow._session  # noqa: SLF001


async def test_edit_the_table(hass: HomeAssistant, covers) -> None:
    """The table shows the stored points; an edited table is checked, reviewed, saved and used (#40)."""
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    subentry_id = next(iter(entry.subentries))
    stored = {
        "window_height_cm": 140,
        "points": {"up": [[0.34, 0.09], [0.53, 0.3], [0.73, 0.6]], "down": [[0.34, 0.01], [0.53, 0.22]]},
        "slit": {"up": 0.2},
    }
    hass.config_entries.async_update_subentry(
        entry,
        entry.subentries[subentry_id],
        data={**entry.subentries[subentry_id].data, "calibration": stored},
    )
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"), context={"source": "reconfigure", "subentry_id": subentry_id}
    )
    flow_id = result["flow_id"]
    await hass.config_entries.subentries.async_configure(flow_id, {"next_step_id": "calibrate"})
    result = await hass.config_entries.subentries.async_configure(flow_id, {"next_step_id": "cal_table"})
    assert result["step_id"] == "cal_table"
    defaults = {str(k): k.default() for k in result["data_schema"].schema if callable(k.default)}
    assert defaults["rows"] == [
        {"module": 34, "up": 9, "down": 1},
        {"module": 53, "up": 30, "down": 22},
        {"module": 73, "up": 60},
    ]

    rows = [{"module": 34, "up": 9, "down": 1}, {"module": 34, "up": 30}]  # twice
    result = await hass.config_entries.subentries.async_configure(flow_id, {"rows": rows})
    assert result["errors"] == {"base": "module_twice"}

    rows = [
        {"module": 30, "up": 5, "down": 2},
        {"module": 50, "up": 28, "down": 20},
        {"module": 75, "up": 62, "down": 55},
        {"module": 95, "up": 94, "down": 90},
    ]
    result = await hass.config_entries.subentries.async_configure(
        flow_id, {"rows": rows, "slit_up": 18, "slit_down": 18}
    )
    assert result["step_id"] == "cal_table_review"
    assert "↑" in result["description_placeholders"]["summary"]
    result = await hass.config_entries.subentries.async_configure(flow_id, {})
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()
    saved = entry.subentries[subentry_id].data["calibration"]
    assert saved["window_height_cm"] == 140
    assert saved["points"]["down"][1] == [0.5, 0.2]
    assert saved["slit"] == {"up": 0.18, "down": 0.18}
    assert entry.runtime_data.shutters[subentry_id].calibration.calibrated


async def test_edit_the_horizon_table(hass: HomeAssistant, covers) -> None:
    """The horizon table is prefilled, checked and saved to the shutter."""
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    subentry_id = next(iter(entry.subentries))
    hass.config_entries.async_update_subentry(
        entry,
        entry.subentries[subentry_id],
        data={**entry.subentries[subentry_id].data, "horizon": [[120, 12.5], [240, 28]]},
    )
    await hass.async_block_till_done()
    result = await open_menu(hass, entry, subentry_id, "horizon")
    assert result["step_id"] == "horizon"
    flow_id = result["flow_id"]
    defaults = {str(k): k.default() for k in result["data_schema"].schema if callable(k.default)}
    assert defaults["rows"] == [{"azimuth": 120.0, "elevation": 12.5}, {"azimuth": 240.0, "elevation": 28.0}]

    flow = hass.config_entries.subentries._progress[flow_id]  # noqa: SLF001
    result = await flow.async_step_horizon({"rows": [{"azimuth": 361, "elevation": 12}]})
    assert result["step_id"] == "horizon" and result["errors"] == {"base": "azimuth_range"}
    result = await hass.config_entries.subentries.async_configure(
        flow_id, {"rows": [{"azimuth": 120, "elevation": 12}, {"azimuth": 120, "elevation": 20}]}
    )
    assert result["step_id"] == "horizon" and result["errors"] == {"base": "azimuth_twice"}
    result = await flow.async_step_horizon({"rows": [{"azimuth": 120, "elevation": 61}]})
    assert result["step_id"] == "horizon" and result["errors"] == {"base": "elevation_range"}

    result = await hass.config_entries.subentries.async_configure(
        flow_id, {"rows": [{"azimuth": 200, "elevation": 35.5}, {"azimuth": 100, "elevation": 10}]}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()
    assert entry.subentries[subentry_id].data["horizon"] == [[100.0, 10.0], [200.0, 35.5]]

    result = await open_menu(hass, entry, subentry_id, "horizon")
    flow_id = result["flow_id"]
    result = await hass.config_entries.subentries.async_configure(flow_id, {"rows": []})
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()
    assert entry.subentries[subentry_id].data["horizon"] == []


async def test_a_module_that_reports_only_when_asked_is_polled(
    hass: HomeAssistant, covers, fast, monkeypatch
) -> None:
    """The module moves but never reports by itself: the assistant asks for its position every few
    seconds and goes on as soon as the target is there, instead of waiting until it gives up."""
    monkeypatch.setattr(assistant, "REFRESH", 0.05)
    monkeypatch.setattr(assistant, "STABLE", 1.5)  # would give up long before without polling
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    controller = entry.runtime_data.shutters[next(iter(entry.subentries))]
    physical_position = {"value": 100}
    refreshes: list[int] = []

    async def set_position(call: ServiceCall) -> None:
        physical_position["value"] = position_of(call)  # moves, but tells nobody

    async def update_entity(call: ServiceCall) -> None:
        refreshes.append(physical_position["value"])
        hass.states.async_set(
            LIVING, "open", {"current_position": physical_position["value"], "supported_features": 15}
        )

    register_moves(hass, set_position)
    hass.services.async_register("homeassistant", "update_entity", update_entity)
    session = assistant.CalibrationSession(controller)
    start = asyncio.get_running_loop().time()
    await session.move(40)
    assert session.reached and refreshes
    assert asyncio.get_running_loop().time() - start < 1.0
