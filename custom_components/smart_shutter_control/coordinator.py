"""Base controller: reads the inputs once per tick and lets every shutter controller evaluate."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_OUTDOOR,
    CONF_PV_POWER,
    CONF_WIND_GUST,
    CONF_WIND_SPEED,
    DEFAULT_OPTIONS,
    DOMAIN,
    INPUT_DEBOUNCE,
    SUBENTRY_SHUTTER,
    TICK_SECONDS,
)
from .controller import ShutterController
from .core.model import Inputs
from .storage import RuntimeStore

_LOGGER = logging.getLogger(__name__)


class BaseCoordinator(DataUpdateCoordinator[None]):
    """Observer for the entities: they refresh when a tick or a cover change is done."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN)
        self.entry = entry
        self.sources = dict(entry.data)
        self.options = {**DEFAULT_OPTIONS, **entry.options}
        self.store = RuntimeStore(hass, entry.entry_id)
        self.shutters: dict[str, ShutterController] = {}
        self.inputs = Inputs(now=time.time())
        self._unsubs: list = []
        self._pending = None

    async def async_start(self) -> None:
        await self.store.async_load()
        for subentry in self.entry.subentries.values():
            if subentry.subentry_type == SUBENTRY_SHUTTER:
                self.shutters[subentry.subentry_id] = ShutterController(self.hass, subentry, self.store)
        self.store.forget(set(self.shutters))
        covers = [s.config.cover for s in self.shutters.values()]
        inputs = [e for e in self._input_entities() if e]
        self._unsubs += [
            async_track_time_interval(self.hass, self._on_tick, timedelta(seconds=TICK_SECONDS)),
            async_track_state_change_event(self.hass, covers, self._on_cover),
            async_track_state_change_event(self.hass, inputs, self._on_input),
        ]
        self.data = None

    async def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        if self._pending:
            self._pending()
            self._pending = None

    def _input_entities(self) -> list[str | None]:
        pv = self.sources.get(CONF_PV_POWER) or []
        return [
            self.sources.get(CONF_OUTDOOR),
            self.sources.get(CONF_WIND_SPEED),
            self.sources.get(CONF_WIND_GUST),
            *pv,
        ]

    def _number(self, entity_id: str | None) -> float | None:
        state = self.hass.states.get(entity_id) if entity_id else None
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return None
        try:
            return float(state.state)
        except ValueError:
            return None

    def read_inputs(self) -> Inputs:
        pv_values = [self._number(e) for e in self.sources.get(CONF_PV_POWER) or []]
        known = [v for v in pv_values if v is not None]
        return Inputs(
            now=time.time(),
            outdoor=self._number(self.sources.get(CONF_OUTDOOR)),
            pv_power=sum(known) if known else None,
            wind=self._number(self.sources.get(CONF_WIND_SPEED)),
            gust=self._number(self.sources.get(CONF_WIND_GUST)),
        )

    async def async_tick(self) -> None:
        self.inputs = self.read_inputs()
        for controller in self.shutters.values():
            await controller.async_evaluate(self.inputs)
        self.async_set_updated_data(None)

    async def _on_tick(self, _now: datetime) -> None:
        await self.async_tick()

    @callback
    def _on_cover(self, event: Event[EventStateChangedData]) -> None:
        for controller in self.shutters.values():
            if controller.config.cover == event.data["entity_id"]:
                controller.observe()
        self.async_update_listeners()  # positions shown by our entities

    @callback
    def _on_input(self, _event: Event[EventStateChangedData]) -> None:
        if self._pending:
            return

        async def _run(_now: datetime) -> None:
            self._pending = None
            await self.async_tick()

        self._pending = async_call_later(self.hass, INPUT_DEBOUNCE, _run)
