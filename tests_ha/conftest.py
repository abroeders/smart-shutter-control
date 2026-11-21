"""Fixtures: two physical shutters, an outdoor sensor and the integration enabled."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from homeassistant.core import HomeAssistant, ServiceCall
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


ENDS = {"open_cover": 100, "close_cover": 0}  # the ends go by the module's own open/close


def position_of(call: ServiceCall) -> int:
    """The position a move of the physical cover asks for."""
    return ENDS[call.service] if call.service in ENDS else int(call.data["position"])


def register_moves(hass: HomeAssistant, handler) -> None:
    for service in ("set_cover_position", *ENDS):
        hass.services.async_register("cover", service, handler)


def mock_moves(hass: HomeAssistant) -> list[SimpleNamespace]:
    """Records the moves of the physical cover; an end by open/close is recorded as position 100 or 0."""
    calls: list[SimpleNamespace] = []

    async def record(call: ServiceCall) -> None:
        calls.append(SimpleNamespace(service=call.service, data={**call.data, "position": position_of(call)}))

    register_moves(hass, record)
    return calls
