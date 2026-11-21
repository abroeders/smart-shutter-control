"""Base controller: reads the inputs once per tick and lets every shutter controller evaluate."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

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
    CONF_LIGHT,
    CONF_LUX_LIMIT,
    CONF_OUTDOOR,
    CONF_PV_PEAK,
    CONF_PV_POWER,
    CONF_SUN_SOURCE,
    CONF_WEATHER,
    CONF_WIND_GUST,
    CONF_WIND_SPEED,
    DEFAULT_LUX_LIMIT,
    DEFAULT_OPTIONS,
    DOMAIN,
    INPUT_DEBOUNCE,
    OPT_CLOSE_ABOVE,
    OPT_CLOSE_BELOW,
    OPT_CLOSE_DELAY,
    OPT_FROST_LIMIT,
    OPT_FROST_RELEASE,
    OPT_HEAT_OUTDOOR,
    OPT_HEAT_ROOM,
    OPT_HOLIDAY_CALENDAR,
    OPT_HOLIDAYS_DISABLED,
    OPT_HOLIDAYS_EXCLUDED,
    OPT_HOLIDAYS_EXTRA,
    OPT_LANGUAGE,
    OPT_MAX_INCIDENCE,
    OPT_OPEN_DELAY,
    OPT_SCHEDULE,
    OPT_STORM_GUST_LIMIT,
    OPT_STORM_LIMIT,
    OPT_STORM_RELEASE,
    OPT_STORM_WIND_LIMIT,
    OPT_SUNNY_THRESHOLD,
    OPT_WEEKEND_DAYS,
    OPT_WINTER_LIMIT,
    SUBENTRY_SHUTTER,
    TICK_SECONDS,
)
from .controller import ShutterController
from .core.heat import SunSettings
from .core.model import Inputs
from .core.schedule import HolidayCalendar, parse_holidays, weekend_set
from .core.sun import SunPosition
from .core.sunny import ClearSkyReference, LuxBaseline, PvBaseline, SunnyDetector
from .core.weather import FrostDetector, StormDetector, cloud_coverage
from .core.winter import OutdoorMean, WinterDetector
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


def _num(value) -> float | None:
    return None if value in (None, "") else float(value)


class BaseCoordinator(DataUpdateCoordinator[None]):
    """Observer for the entities: they refresh when a tick or a cover change is done."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN)
        self.entry = entry
        self.sources = dict(entry.data)
        self.options = {**DEFAULT_OPTIONS, **entry.options}
        if OPT_STORM_LIMIT in entry.options and OPT_STORM_GUST_LIMIT not in entry.options:
            self.options[OPT_STORM_GUST_LIMIT] = entry.options[OPT_STORM_LIMIT]  # the one limit of 0.1–0.3
        o = self.options
        self.storm = StormDetector(
            _num(o.get(OPT_STORM_WIND_LIMIT)),
            _num(o.get(OPT_STORM_GUST_LIMIT)),
            float(o[OPT_STORM_RELEASE]) * 60,
        )
        self.frost = FrostDetector(float(o[OPT_FROST_LIMIT]), float(o[OPT_FROST_RELEASE]) * 60)
        self.safety = {
            "close_above": _num(o.get(OPT_CLOSE_ABOVE)),
            "close_below": _num(o.get(OPT_CLOSE_BELOW)),
        }
        self._quick = None
        self.outdoor_mean = OutdoorMean()
        self.winter = WinterDetector(float(o[OPT_WINTER_LIMIT]))
        self.language: str | None = None if o[OPT_LANGUAGE] == "system" else str(o[OPT_LANGUAGE])
        self.entity_names: dict[str, str] = {}
        self.store = RuntimeStore(hass, entry.entry_id)
        self.shutters: dict[str, ShutterController] = {}
        self.inputs = Inputs(now=time.time())
        self.sunny = SunnyDetector()
        self.weather_state: str | None = None
        self.cloud_coverage: float | None = None
        self.calendar = self._holiday_calendar()
        self.base_device_id: str | None = None
        self._unsubs: list = []
        self._pending = None

    @property
    def sun_source(self) -> str:
        return str(self.sources.get(CONF_SUN_SOURCE) or ("pv" if self.sources.get(CONF_PV_POWER) else "none"))

    @property
    def reference_key(self) -> str:
        """PV and lux keep their own learned reference, so switching back does not start from zero."""
        return "clear_sky_lux" if self.sun_source == "light" else "clear_sky"

    @property
    def sunny_threshold(self) -> float:
        return float(self.options[OPT_SUNNY_THRESHOLD]) / 100

    def baseline(self) -> PvBaseline | LuxBaseline:
        if self.sun_source == "light":
            return LuxBaseline(float(self.sources.get(CONF_LUX_LIMIT) or DEFAULT_LUX_LIMIT))
        return PvBaseline(self.sources.get(CONF_PV_PEAK))

    def sun_value(self) -> float | None:
        """PV power (sum) or illuminance (highest sensor), by the sun source; None without one."""
        if self.sun_source == "pv":
            known = [
                v for v in (self._number(e) for e in self.sources.get(CONF_PV_POWER) or []) if v is not None
            ]
            return sum(known) if known else None
        if self.sun_source == "light":
            known = [
                v for v in (self._number(e) for e in self.sources.get(CONF_LIGHT) or []) if v is not None
            ]
            return max(known) if known else None
        return None

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
        if self.language:
            self.entity_names = await self.hass.async_add_executor_job(entity_names, self.language)
        self.outdoor_mean = OutdoorMean.from_dict(self.store.globals.get("outdoor_mean"))
        self.winter.mode = str(self.store.globals.get("winter_mode", "auto"))
        self.sunny = SunnyDetector(
            reference=ClearSkyReference.from_dict(self.store.globals.get(self.reference_key)),
            threshold=self.sunny_threshold,
            baseline=self.baseline(),
        )
        sun = self.sun_settings()
        base_schedule = dict(self.options.get(OPT_SCHEDULE) or {})
        for subentry in self.entry.subentries.values():
            if subentry.subentry_type == SUBENTRY_SHUTTER:
                controller = ShutterController(
                    self.hass,
                    subentry,
                    self.store,
                    sun=sun,
                    base_schedule=base_schedule,
                    calendar=self.calendar,
                    safety=self.safety,
                )
                controller.on_manual = self._on_manual
                if self.sun_source == "light":
                    controller.use_facade(self.sunny_threshold, self.baseline())
                self.shutters[subentry.subentry_id] = controller
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
        await self.store.async_flush()
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        if self._pending:
            self._pending()
            self._pending = None
        if self._quick:
            self._quick()
            self._quick = None

    def _input_entities(self) -> list[str | None]:
        source = {"pv": CONF_PV_POWER, "light": CONF_LIGHT}.get(self.sun_source)
        sensors = (self.sources.get(source) or []) if source else []
        facades = [s.facade_light for s in self.shutters.values() if s.facade_light]
        return [
            self.sources.get(CONF_OUTDOOR),
            self.sources.get(CONF_WIND_SPEED),
            self.sources.get(CONF_WIND_GUST),
            *sensors,
            *facades,
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
        now = time.time()
        sun = SunPosition.at(self.hass.config.latitude, self.hass.config.longitude, now)
        weather = self.hass.states.get(self.sources[CONF_WEATHER]) if self.sources.get(CONF_WEATHER) else None
        value = self.sun_value()
        self.weather_state = weather.state if weather else None
        self.cloud_coverage = cloud_coverage(dict(weather.attributes)) if weather else None
        sunny = self.sunny.update(sun, value, self.weather_state, now)
        if value is not None:
            self.store.set_global(self.reference_key, self.sunny.reference.to_dict())
        outdoor = self._number(self.sources.get(CONF_OUTDOOR))
        storm = self.storm.update(
            self._number(self.sources.get(CONF_WIND_SPEED)),
            self._number(self.sources.get(CONF_WIND_GUST)),
            now,
        )
        frost = self.frost.update(outdoor, now)
        before = len(self.outdoor_mean.samples)
        self.outdoor_mean.add(outdoor, now)
        if len(self.outdoor_mean.samples) != before:
            self.store.set_global("outdoor_mean", self.outdoor_mean.to_dict())
        winter = self.winter.update(self.outdoor_mean.mean(now))
        return Inputs(
            winter=winter,
            now=now,
            storm=storm,
            frost=frost,
            sun=sun,
            sunny=sunny,
            sun_factor=self.sunny.factor,
            outdoor=self._number(self.sources.get(CONF_OUTDOOR)),
            pv_power=value if self.sun_source == "pv" else None,
            wind=self._number(self.sources.get(CONF_WIND_SPEED)),
            gust=self._number(self.sources.get(CONF_WIND_GUST)),
        )

    async def async_tick(self) -> None:
        self.inputs = self.read_inputs()
        for controller in self.shutters.values():
            await controller.async_evaluate(self.inputs, weather=self.weather_state)
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

    def set_winter_mode(self, mode: str) -> None:
        self.winter.mode = mode
        self.store.set_global("winter_mode", mode)

    @callback
    def _on_manual(self) -> None:
        """A manual move during a storm is put back at once, not at the next minute."""
        if not self.storm.active or self._quick:
            return

        async def _run(_now: datetime) -> None:
            self._quick = None
            await self.async_tick()

        self._quick = async_call_later(self.hass, 3, _run)

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


def entity_names(language: str) -> dict[str, str]:
    """Entity names by translation key in one of the integration's own languages (#9)."""
    path = Path(__file__).parent / "translations" / f"{language}.json"
    if not path.exists():
        return {}
    entities = json.loads(path.read_text(encoding="utf-8")).get("entity", {})
    return {key: v["name"] for platform in entities.values() for key, v in platform.items() if v.get("name")}
