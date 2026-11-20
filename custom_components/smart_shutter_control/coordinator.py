"""Base controller: reads the inputs once per tick and lets every shutter controller evaluate."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_change,
    async_track_time_interval,
)
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_OUTDOOR,
    CONF_PV_PEAK,
    CONF_PV_POWER,
    CONF_WEATHER,
    CONF_WIND_GUST,
    CONF_WIND_SPEED,
    DEFAULT_OPTIONS,
    DOMAIN,
    INPUT_DEBOUNCE,
    OPT_CLOSE_DELAY,
    OPT_HEAT_OUTDOOR,
    OPT_HEAT_ROOM,
    OPT_HOLIDAY_CALENDAR,
    OPT_HOLIDAYS_DISABLED,
    OPT_HOLIDAYS_EXCLUDED,
    OPT_HOLIDAYS_EXTRA,
    OPT_MAX_INCIDENCE,
    OPT_OPEN_DELAY,
    OPT_SCHEDULE,
    OPT_SUNNY_THRESHOLD,
    OPT_WEEKEND_DAYS,
    SUBENTRY_SHUTTER,
    TICK_SECONDS,
)
from .controller import ShutterController
from .core.heat import SunSettings
from .core.model import Inputs
from .core.schedule import HolidayCalendar, parse_holidays, weekend_set
from .core.sun import SunPosition
from .core.sunny import ClearSkyReference, SunnyDetector
from .storage import RuntimeStore

_LOGGER = logging.getLogger(__name__)


async def read_calendar(hass: HomeAssistant, entity_id: str) -> dict | None:
    """Holidays (date → name) of the coming 400 days from a calendar entity; None when it cannot be read."""
    start = dt_util.now()
    try:
        response = await hass.services.async_call(
            "calendar",
            "get_events",
            {
                "entity_id": entity_id,
                "start_date_time": start.isoformat(),
                "end_date_time": (start + timedelta(days=400)).isoformat(),
            },
            blocking=True,
            return_response=True,
        )
    except (HomeAssistantError, ValueError) as err:
        _LOGGER.warning("Could not read holidays from %s: %s", entity_id, err)
        return None
    days = {}
    for event in (response or {}).get(entity_id, {}).get("events", []):
        day = dt_util.parse_date(str(event.get("start", ""))[:10])
        if day is not None:
            days[day] = str(event.get("summary") or "")
    return days


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
        self.sunny = SunnyDetector()
        self.calendar = self._holiday_calendar()
        self.base_device_id: str | None = None
        self._unsubs: list = []
        self._pending = None

    def sun_settings(self) -> SunSettings:
        o = self.options
        return SunSettings(
            max_incidence=float(o[OPT_MAX_INCIDENCE]),
            heat_outdoor=float(o[OPT_HEAT_OUTDOOR]),
            heat_room=float(o[OPT_HEAT_ROOM]),
            close_delay=float(o[OPT_CLOSE_DELAY]) * 60,
            open_delay=float(o[OPT_OPEN_DELAY]) * 60,
        )

    async def async_start(self) -> None:
        await self.store.async_load()
        self.sunny = SunnyDetector(
            reference=ClearSkyReference.from_dict(self.store.globals.get("clear_sky")),
            threshold=float(self.options[OPT_SUNNY_THRESHOLD]) / 100,
            pv_peak_kw=self.sources.get(CONF_PV_PEAK),
        )
        sun = self.sun_settings()
        base_schedule = dict(self.options.get(OPT_SCHEDULE) or {})
        for subentry in self.entry.subentries.values():
            if subentry.subentry_type == SUBENTRY_SHUTTER:
                self.shutters[subentry.subentry_id] = ShutterController(
                    self.hass,
                    subentry,
                    self.store,
                    sun=sun,
                    base_schedule=base_schedule,
                    calendar=self.calendar,
                )
        self.store.forget(set(self.shutters))
        watched = [s.config.cover for s in self.shutters.values()]
        watched += [s.adapter.power_entity for s in self.shutters.values() if s.adapter.power_entity]
        inputs = [e for e in self._input_entities() if e]
        await self.async_refresh_holidays()
        self._unsubs += [
            async_track_time_interval(self.hass, self._on_tick, timedelta(seconds=TICK_SECONDS)),
            async_track_state_change_event(self.hass, watched, self._on_cover),
            async_track_state_change_event(self.hass, inputs, self._on_input),
            async_track_time_change(self.hass, self._on_midnight, hour=0, minute=5, second=0),
        ]
        calendar_entity = self.options.get(OPT_HOLIDAY_CALENDAR)
        if calendar_entity:
            # the calendar's integration may start after this one: read it once it is there
            self._unsubs.append(
                async_track_state_change_event(self.hass, [calendar_entity], self._on_calendar)
            )
            self._unsubs.append(async_at_started(self.hass, self._on_started))
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
        now = time.time()
        sun = SunPosition.at(self.hass.config.latitude, self.hass.config.longitude, now)
        weather = self.hass.states.get(self.sources[CONF_WEATHER]) if self.sources.get(CONF_WEATHER) else None
        pv = sum(known) if known else None
        sunny = self.sunny.update(sun, pv, weather.state if weather else None, now)
        if pv is not None:
            self.store.set_global("clear_sky", self.sunny.reference.to_dict())
        return Inputs(
            now=now,
            sun=sun,
            sunny=sunny,
            sun_factor=self.sunny.factor,
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

    def _holiday_calendar(self) -> HolidayCalendar:
        extra, _ = parse_holidays(self.options.get(OPT_HOLIDAYS_EXTRA))
        excluded, _ = parse_holidays(self.options.get(OPT_HOLIDAYS_EXCLUDED))
        return HolidayCalendar(
            weekend_set(self.options.get(OPT_WEEKEND_DAYS)),
            extra,
            excluded,
            disabled=frozenset(self.options.get(OPT_HOLIDAYS_DISABLED) or []),
        )

    async def async_refresh_holidays(self) -> None:
        """Read the public holidays of the coming 400 days from the calendar entity, if one is set."""
        entity_id = self.options.get(OPT_HOLIDAY_CALENDAR)
        if not entity_id:
            self.calendar.from_calendar = {}
            return
        days = await read_calendar(self.hass, entity_id)
        if days is not None:
            self.calendar.from_calendar = days

    async def _on_midnight(self, _now: datetime) -> None:
        await self.async_refresh_holidays()

    async def _on_started(self, _hass: HomeAssistant) -> None:
        await self.async_refresh_holidays()

    async def _on_calendar(self, event: Event[EventStateChangedData]) -> None:
        old = event.data.get("old_state")
        if old is None or old.state in (STATE_UNAVAILABLE, STATE_UNKNOWN) or not self.calendar.from_calendar:
            await self.async_refresh_holidays()
            self.async_update_listeners()

    def set_sleep_in_all(self, on: bool) -> None:
        for controller in self.shutters.values():
            controller.set_sleep_in(on)

    @property
    def sleep_in_all(self) -> bool:
        return bool(self.shutters) and all(c.sleep_in.armed for c in self.shutters.values())

    @callback
    def _on_cover(self, event: Event[EventStateChangedData]) -> None:
        entity_id = event.data["entity_id"]
        for controller in self.shutters.values():
            if entity_id in (controller.config.cover, controller.adapter.power_entity):
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
