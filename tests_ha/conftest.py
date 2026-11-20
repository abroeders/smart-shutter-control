"""Fixtures: two physical shutters, an outdoor sensor and the integration enabled."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.smart_shutter_control.const import DEFAULT_OPTIONS, DOMAIN

pytest_plugins = "pytest_homeassistant_custom_component"

OUTDOOR = "sensor.outdoor_temperature"
LIVING = "cover.living_room"
BEDROOM = "cover.bedroom"
GARAGE = "cover.garage_door"  # open/close only, no position


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    return


@pytest.fixture
def covers(hass: HomeAssistant) -> None:
    hass.states.async_set(OUTDOOR, "12.0", {"device_class": "temperature", "unit_of_measurement": "°C"})
    for entity_id, name in ((LIVING, "Living room"), (BEDROOM, "Bedroom")):
        hass.states.async_set(
            entity_id, "open", {"current_position": 100, "supported_features": 15, "friendly_name": name}
        )
    hass.states.async_set(GARAGE, "closed", {"supported_features": 3, "friendly_name": "Garage door"})


async def add_shutter(hass: HomeAssistant, entry, cover: str, **extra):
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "shutter"), context={"source": "user"}
    )
    data = {
        "cover": cover,
        "azimuth": 180,
        "tilt": 90,
        "min_elevation": 0,
        "max_elevation": 90,
        "max_position": 100,
        **extra,
    }
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], data)
    await hass.async_block_till_done()
    return result


async def setup_base(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, title="House", data={"outdoor_temperature": OUTDOOR}, options=dict(DEFAULT_OPTIONS)
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
