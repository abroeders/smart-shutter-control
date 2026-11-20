"""Light sensors as the sun source: the choice, the saturation note, migration and a facade sensor."""

from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.smart_shutter_control.const import DEFAULT_OPTIONS, DOMAIN

from .conftest import LIVING, OUTDOOR, add_shutter
from .test_schedule import amsterdam, eid, report  # noqa: F401  (fixture)

LUX_A, LUX_B, FACADE = "sensor.lux_garden", "sensor.lux_roof", "sensor.lux_facade"


def lux(hass: HomeAssistant, entity_id: str, value: float) -> None:
    hass.states.async_set(entity_id, str(value), {"device_class": "illuminance", "unit_of_measurement": "lx"})


async def setup_light(hass: HomeAssistant, **data) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="House",
        data={"outdoor_temperature": OUTDOOR, "sun_source": "light", "light_sensors": [LUX_A, LUX_B], **data},
        options=dict(DEFAULT_OPTIONS),
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_light_source_flow_and_saturation_note(hass: HomeAssistant) -> None:
    lux(hass, LUX_A, 500)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"name": "House"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"outdoor_temperature": OUTDOOR, "sun_source": "light"}
    )
    assert result["step_id"] == "light"
    assert {str(k) for k in result["data_schema"].schema} == {"light_sensors", "lux_limit"}
    with patch("custom_components.smart_shutter_control.config_flow._max_30_days", return_value="2000"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"light_sensors": [LUX_A], "lux_limit": 30000}
        )
        assert result["errors"] == {"base": "saturates"}  # said once …
        assert "2000 lx" in result["description_placeholders"]["maxima"]
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"light_sensors": [LUX_A], "lux_limit": 30000}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY  # … then saved anyway
    assert "pv_power" not in result["data"] and result["data"]["light_sensors"] == [LUX_A]


async def test_switching_source_drops_the_other_fields(hass: HomeAssistant) -> None:
    entry = await setup_light(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "reconfigure", "entry_id": entry.entry_id}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"outdoor_temperature": OUTDOOR, "sun_source": "pv"}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"pv_power": ["sensor.pv"]})
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()
    assert entry.data["sun_source"] == "pv" and "light_sensors" not in entry.data


async def test_old_entries_get_a_sun_source(hass: HomeAssistant) -> None:
    for data, expected in (({"pv_power": ["sensor.pv"]}, "pv"), ({}, "none")):
        entry = MockConfigEntry(domain=DOMAIN, data={"outdoor_temperature": OUTDOOR, **data})
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.data["sun_source"] == expected
        await hass.config_entries.async_unload(entry.entry_id)


async def test_highest_light_sensor_and_a_facade_sensor(hass: HomeAssistant, covers, amsterdam) -> None:  # noqa: F811
    amsterdam.move_to("2026-11-18 12:30:00+01:00")
    lux(hass, LUX_A, 10000)
    lux(hass, LUX_B, 45000)
    lux(hass, FACADE, 5000)
    report(hass, 100)
    entry = await setup_light(hass)
    sun_factor = eid(hass, entry, "sensor", "sun_factor", shutter=False)
    await add_shutter(hass, entry, LIVING, light_sensor=FACADE)
    coordinator = entry.runtime_data
    coordinator.inputs = coordinator.read_inputs()
    assert coordinator.inputs.sun.elevation > 10
    assert coordinator.sunny.value == 45000 and coordinator.sun_source == "light"
    assert coordinator.sunny.source == "lux_limit" and coordinator.sunny.sunny
    controller = next(iter(coordinator.shutters.values()))
    inputs = controller._with_facade(coordinator.inputs)
    assert not inputs.sunny  # the facade sensor sees no sun at this window
    await coordinator.async_tick()
    await hass.async_block_till_done()
    assert hass.states.get(sun_factor).attributes["lux"] == 45000
    window = hass.states.get(eid(hass, entry, "binary_sensor", "sun_on_window"))
    assert window.attributes["lux"] == 5000 and window.attributes["sunny"] is False


async def test_facade_field_only_with_light_sensors(hass: HomeAssistant, covers) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={"outdoor_temperature": OUTDOOR, "sun_source": "pv"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"), context={"source": "user"}
    )
    assert "light_sensor" not in {str(k) for k in result["data_schema"].schema}
    light = await setup_light(hass)
    result = await hass.config_entries.subentries.async_init(
        (light.entry_id, "shutter"), context={"source": "user"}
    )
    assert "light_sensor" in {str(k) for k in result["data_schema"].schema}
