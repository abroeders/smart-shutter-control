"""Adding the base controller, its options, and adding, changing and removing shutters."""

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM
from pytest_homeassistant_custom_component.common import MockConfigEntry

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
        result["flow_id"], {"outdoor_temperature": OUTDOOR, "sun_source": "pv"}
    )
    assert result["step_id"] == "pv"  # only the PV fields
    assert {str(k) for k in result["data_schema"].schema} == {"pv_power", "pv_peak"}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"pv_power": ["sensor.pv"]})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["sun_source"] == "pv" and result["data"]["pv_power"] == ["sensor.pv"]
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


async def test_us_storm_options_show_and_store_mph(hass: HomeAssistant, covers) -> None:
    hass.config.units = US_CUSTOMARY_SYSTEM
    entry = await setup_base(hass)

    async def max_wind(hass, entity_id, wind=False):
        return "40 mph" if wind else "not used"

    with patch("custom_components.smart_shutter_control.options_flow._max_30_days", new=max_wind):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": "storm"}
        )

    assert result["step_id"] == "storm"
    assert result["description_placeholders"] == {"wind_max": "40 mph", "gust_max": "40 mph"}
    gust = next(k for k in result["data_schema"].schema if str(k) == "storm_gust_limit")
    frost = next(k for k in result["data_schema"].schema if str(k) == "frost_limit")
    assert frost.default() == 32
    gust_validator = result["data_schema"].schema[gust]
    gust_config = gust_validator.config
    assert gust_config["unit_of_measurement"] == "mph"
    assert gust_config["step"] == 1
    assert (gust.description or {}).get("suggested_value") == 37

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "storm_gust_limit": 40,
            "storm_release": 15,
            "frost_limit": 32,
            "frost_release": 60,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["storm_gust_limit"] == pytest.approx(64.4)
    assert entry.options["frost_limit"] == 0


async def test_us_sun_options_keep_stored_celsius(hass: HomeAssistant, covers) -> None:
    hass.config.units = US_CUSTOMARY_SYSTEM
    entry = await setup_base(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "sun"})
    suggested = result["data_schema"]({})
    assert suggested["heat_outdoor"] == 72
    assert suggested["heat_room"] == 75

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "sunny_threshold": suggested["sunny_threshold"] or 60,
            "max_incidence": suggested["max_incidence"] or 85,
            "heat_outdoor": suggested["heat_outdoor"],
            "heat_room": suggested["heat_room"],
            "hot_day": 82,
            "close_delay": suggested["close_delay"] or 5,
            "open_delay": suggested["open_delay"] or 20,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["heat_outdoor"] == 22
    assert entry.options["heat_room"] == 24
    assert entry.options["hot_day"] == 28


async def test_us_shutter_lengths_show_and_store_unchanged_or_changed(hass: HomeAssistant, covers) -> None:
    hass.config.units = US_CUSTOMARY_SYSTEM
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING)
    subentry = next(s for s in entry.subentries.values() if s.data["cover"] == LIVING)
    hass.config_entries.async_update_subentry(
        entry,
        subentry,
        data={**subentry.data, "window_sill": 150, "window_height": 140, "sun_depth": 2.5},
    )
    await hass.async_block_till_done()
    subentry = entry.subentries[subentry.subentry_id]

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "settings"}
    )
    suggested = {str(k): (k.description or {}).get("suggested_value") for k in result["data_schema"].schema}
    validators = {str(k): v for k, v in result["data_schema"].schema.items()}
    assert suggested["window_sill"] == 59
    assert suggested["window_height"] == 55
    assert suggested["sun_depth"] == 8
    assert validators["window_sill"].config["unit_of_measurement"] == "in"
    assert validators["window_height"].config["unit_of_measurement"] == "in"
    assert validators["sun_depth"].config["unit_of_measurement"] == "ft"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            "cover": LIVING,
            "azimuth": 180,
            "tilt": 90,
            "min_elevation": 0,
            "max_elevation": 90,
            "max_position": 100,
            "window_sill": suggested["window_sill"],
            "window_height": suggested["window_height"],
            "sun_depth": suggested["sun_depth"],
        },
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()
    data = entry.subentries[subentry.subentry_id].data
    assert data["window_sill"] == 150
    assert data["window_height"] == 140
    assert data["sun_depth"] == 2.5

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "settings"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            "cover": LIVING,
            "azimuth": 180,
            "tilt": 90,
            "min_elevation": 0,
            "max_elevation": 90,
            "max_position": 100,
            "window_sill": 40,
            "window_height": 60,
            "sun_depth": 10,
        },
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()
    data = entry.subentries[subentry.subentry_id].data
    assert data["window_sill"] == pytest.approx(101.6)
    assert data["window_height"] == pytest.approx(152.4)
    assert data["sun_depth"] == pytest.approx(3.05)


async def test_us_shutter_heat_limits_and_schedule_override_use_fahrenheit(
    hass: HomeAssistant, covers
) -> None:
    hass.config.units = US_CUSTOMARY_SYSTEM
    entry = await setup_base(hass)
    await add_shutter(hass, entry, LIVING, heat_outdoor=50, heat_room=68)
    subentry = next(s for s in entry.subentries.values() if s.data["cover"] == LIVING)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "settings"}
    )
    suggested = {str(k): (k.description or {}).get("suggested_value") for k in result["data_schema"].schema}
    validators = {str(k): v for k, v in result["data_schema"].schema.items()}
    assert suggested["heat_outdoor"] == 50
    assert suggested["heat_room"] == 68
    assert validators["heat_outdoor"].config["unit_of_measurement"] == "°F"
    assert validators["heat_room"].config["unit_of_measurement"] == "°F"

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "schedule"}
    )
    winter = next(k for k in result["data_schema"].schema if str(k) == "winter_closed_below")
    winter_validator = result["data_schema"].schema[winter]
    assert winter_validator.config["unit_of_measurement"] == "°F"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"winter_closed_below": 23}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()
    assert entry.subentries[subentry.subentry_id].data["schedule"]["winter_closed_below"] == pytest.approx(-5)


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
        "glare_from",
        "glare_position",
        "glare_protection",
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
        "stuck",
        "sun_left",
        "sun_on_window",
    ]
    per_shutter = {e.config_subentry_id for e in entities if e.config_subentry_id}
    assert per_shutter == set(shutters.values())
    base = [e for e in entities if not e.config_subentry_id]
    base_keys = sorted(e.unique_id.removeprefix(f"{entry.entry_id}_") for e in base)
    assert base_keys == [
        "automatic_all",
        "forecast_max",
        "frost",
        "holiday",
        "hot_day",
        "sleep_in_all",
        "storm",
        "sun_factor",
        "sunny",
        "winter",
        "winter_mode",
    ]


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
            "window_sill": 90,
            "window_height": 140,
            "sun_depth": 2.5,
        },
    )
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()
    assert entry.subentries[living.subentry_id].data["azimuth"] == 135
    assert entry.subentries[living.subentry_id].data["window_sill"] == 90
    assert entry.subentries[living.subentry_id].data["window_height"] == 140
    assert entry.subentries[living.subentry_id].data["sun_depth"] == 2.5
    assert entry.runtime_data.shutters[living.subentry_id].config.azimuth == 135

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"), context={"source": "reconfigure", "subentry_id": living.subentry_id}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "settings"}
    )
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
    assert "window_sill" not in entry.subentries[living.subentry_id].data
    assert "window_height" not in entry.subentries[living.subentry_id].data
    assert "sun_depth" not in entry.subentries[living.subentry_id].data

    hass.config_entries.async_remove_subentry(entry, living.subentry_id)
    await hass.async_block_till_done()
    remaining = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    assert remaining and all(living.subentry_id not in e.unique_id for e in remaining)
    assert len(entry.runtime_data.shutters) == 1


async def test_the_unused_pv_forecast_source_is_removed(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="House",
        data={"outdoor_temperature": "sensor.outdoor", "pv_forecast": "sensor.fc"},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert "pv_forecast" not in entry.data
