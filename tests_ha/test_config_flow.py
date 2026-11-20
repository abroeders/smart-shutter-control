"""Adding the base controller, its options, and adding, changing and removing shutters."""

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.smart_shutter_control.const import DOMAIN

from .conftest import BEDROOM, GARAGE, LIVING, OUTDOOR, add_shutter, setup_base


def device(hass: HomeAssistant, identifier: str):
    registry = dr.async_get(hass)
    if hasattr(registry, "async_get_device_by_identifier"):  # Home Assistant 2026.10 and later
        entry_id = hass.config_entries.async_entries(DOMAIN)[0].entry_id
        return registry.async_get_device_by_identifier((DOMAIN, identifier), entry_id)
    return registry.async_get_device(identifiers={(DOMAIN, identifier)})


async def test_base_flow_creates_entry_and_device(hass: HomeAssistant, covers) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"name": "House"})
    assert result["step_id"] == "sources"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"outdoor_temperature": OUTDOOR}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.state is ConfigEntryState.LOADED
    assert entry.options["storm_gust_limit"] == 60 and entry.options["storm_wind_limit"] == 50
    assert device(hass, entry.entry_id).name == "House"


async def test_storm_options(hass: HomeAssistant, covers) -> None:
    entry = await setup_base(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "storm"})
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"storm_gust_limit": 70, "storm_release": 15, "frost_limit": 0, "frost_release": 60},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["storm_gust_limit"] == 70 and entry.options["storm_wind_limit"] is None
    assert entry.runtime_data.storm.gust_limit == 70 and entry.runtime_data.storm.wind_limit is None


async def test_add_shutters_as_devices_under_the_base(hass: HomeAssistant, covers) -> None:
    entry = await setup_base(hass)
    assert (await add_shutter(hass, entry, LIVING))["type"] is FlowResultType.CREATE_ENTRY
    assert (await add_shutter(hass, entry, BEDROOM, name="Master bedroom", azimuth=270))["type"] is (
        FlowResultType.CREATE_ENTRY
    )
    base = device(hass, entry.entry_id)
    shutters = {s.title: s.subentry_id for s in entry.subentries.values()}
    assert set(shutters) == {"Living room", "Master bedroom"}
    for subentry_id in shutters.values():
        assert device(hass, subentry_id).via_device_id == base.id
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    living = shutters["Living room"]
    prefix = f"{entry.entry_id}_{living}_"
    keys = sorted(e.unique_id.removeprefix(prefix) for e in entities if e.unique_id.startswith(prefix))
    assert keys == [
        "automatic",
        "calibration",
        "heat_protection",
        "manual_pause",
        "max_position",
        "next_action",
        "opening",
        "phase",
        "reason",
        "resume",
        "shading_position",
        "shutter",
        "sleep_in",
        "stand",
        "sun_on_window",
    ]
    per_shutter = {e.config_subentry_id for e in entities if e.config_subentry_id}
    assert per_shutter == set(shutters.values())
    base = [e for e in entities if not e.config_subentry_id]
    base_keys = sorted(e.unique_id.removeprefix(f"{entry.entry_id}_") for e in base)
    assert base_keys == ["frost", "holiday", "sleep_in_all", "storm", "sun_factor", "sunny"]


async def test_shutter_flow_errors(hass: HomeAssistant, covers) -> None:
    entry = await setup_base(hass)
    result = await add_shutter(hass, entry, GARAGE)
    assert result["errors"] == {"cover": "no_position"}
    await add_shutter(hass, entry, LIVING)
    result = await add_shutter(hass, entry, LIVING)
    assert result["errors"] == {"cover": "already_configured"}
    result = await add_shutter(hass, entry, BEDROOM, min_elevation=40, max_elevation=30)
    assert result["errors"] == {"max_elevation": "elevation_order"}


async def test_reconfigure_and_remove_a_shutter(hass: HomeAssistant, covers) -> None:
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    await add_shutter(hass, entry, BEDROOM)
    living = next(s for s in entry.subentries.values() if s.data["cover"] == LIVING)
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"), context={"source": "reconfigure", "subentry_id": living.subentry_id}
    )
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "settings"}
    )
    assert result["step_id"] == "settings"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            "cover": LIVING,
            "azimuth": 135,
            "tilt": 90,
            "min_elevation": 5,
            "max_elevation": 90,
            "max_position": 80,
        },
    )
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()
    assert entry.subentries[living.subentry_id].data["azimuth"] == 135
    assert entry.runtime_data.shutters[living.subentry_id].config.azimuth == 135

    hass.config_entries.async_remove_subentry(entry, living.subentry_id)
    await hass.async_block_till_done()
    remaining = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    assert remaining and all(living.subentry_id not in e.unique_id for e in remaining)
    assert len(entry.runtime_data.shutters) == 1
