"""Base controller: reads the inputs once per tick and lets every shutter controller evaluate."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import units
from .const import (
    CONF_LIGHT,
    CONF_LUX_LIMIT,
    CONF_OUTDOOR,
    CONF_PV_AZIMUTH,
    CONF_PV_PEAK,
    CONF_PV_POWER,
    CONF_PV_TILT,
    CONF_SUN_SOURCE,
    CONF_WEATHER,
    CONF_WIND_GUST,
    CONF_WIND_SPEED,
    DEFAULT_LUX_LIMIT,
    DEFAULT_OPTIONS,
    DEFAULT_PV_AZIMUTH,
    DEFAULT_PV_TILT,
    DOMAIN,
    INPUT_DEBOUNCE,
    OPT_CLOSE_ABOVE,
    OPT_CLOSE_BELOW,
    OPT_CLOSE_DELAY,
    OPT_FROST_LIMIT,
    OPT_FROST_RELEASE,
    OPT_HEAT_OUTDOOR,
    OPT_HEAT_ROOM,
    OPT_HOT_DAY,
    OPT_LANGUAGE,
    OPT_MAX_INCIDENCE,
    OPT_OPEN_DELAY,
    OPT_SCHEDULE,
    OPT_STORM_GUST_LIMIT,
    OPT_STORM_LIMIT,
    OPT_STORM_RELEASE,
    OPT_STORM_WIND_LIMIT,
    OPT_SUNNY_THRESHOLD,
    OPT_WINTER_LIMIT,
    SUBENTRY_SHUTTER,
    TICK_SECONDS,
)
from .controller import ShutterController
from .core.heat import SunSettings
from .core.model import Inputs
from .core.sun import SunPosition
from .core.sunny import ClearSkyReference, LuxBaseline, PvBaseline, SunnyDetector
from .core.weather import FrostDetector, StormDetector, cloud_coverage
from .core.winter import OutdoorMean, WinterDetector
from .providers import ForecastProvider, HolidayProvider
from .storage import RuntimeStore

_LOGGER = logging.getLogger(__name__)


def _num(value) -> float | None:
    return None if value in (None, "") else float(value)


class BaseCoordinator(DataUpdateCoordinator[None]):
    """Observer for the entities: they refresh when a tick or a cover change is done."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN)
        self.automatic_all = True  # (#53)
        self.entry = entry
        self._quiet_update = False
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
        self._quick: CALLBACK_TYPE | None = None
        self._settle: CALLBACK_TYPE | None = None  # check arrival after a stop short of the target (#108)
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
        self.forecast = ForecastProvider(hass, self.sources.get(CONF_WEATHER))  # (#50)
        self.holidays = HolidayProvider(hass, self.options)
        self.calendar = self.holidays.calendar  # shared with every schedule, refreshed in place
        self.base_device_id: str | None = None
        self._unsubs: list[CALLBACK_TYPE] = []
        self._pending: CALLBACK_TYPE | None = None
        self._release: CALLBACK_TYPE | None = None  # the evaluation when a closed contact's hold ends (#49)

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

    def _lux_baseline(self) -> LuxBaseline:
        return LuxBaseline(float(self.sources.get(CONF_LUX_LIMIT) or DEFAULT_LUX_LIMIT))

    def baseline(self) -> PvBaseline | LuxBaseline:
        if self.sun_source == "light":
            return self._lux_baseline()
        return PvBaseline(
            self.sources.get(CONF_PV_PEAK),
            float(self.sources.get(CONF_PV_TILT, DEFAULT_PV_TILT)),
            float(self.sources.get(CONF_PV_AZIMUTH, DEFAULT_PV_AZIMUTH)),
        )

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
            hot_day=_num(o.get(OPT_HOT_DAY)),
        )

    async def async_start(self) -> None:
        await self.store.async_load()
        if self.language:
            self.entity_names = await self.hass.async_add_executor_job(entity_names, self.language)
        self.outdoor_mean = OutdoorMean.from_dict(self.store.globals.get("outdoor_mean"))
        self.winter.mode = str(self.store.globals.get("winter_mode", "auto"))
        self.automatic_all = bool(self.store.globals.get("automatic_all", True))  # (#53)
        self.sunny = SunnyDetector(
            reference=ClearSkyReference.from_dict(self.store.globals.get(self.reference_key)),
            threshold=self.sunny_threshold,
            baseline=self.baseline(),
        )
        self._create_shutters()
        await self.holidays.async_refresh()
        await self.forecast.async_refresh()
        self._unsubs += self._track_entities()
        self._unsubs += self.holidays.track(self.async_update_listeners)
        self._unsubs += self.forecast.track(self.async_update_listeners)
        self.data = None

    def _create_shutters(self) -> None:
        """One shutter controller per shutter subentry; the stored state of removed shutters is dropped."""
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
                    controller.use_facade(self.sunny_threshold, self._lux_baseline())
                self.shutters[subentry.subentry_id] = controller
        self.store.forget(set(self.shutters))

    def _track_entities(self) -> list[CALLBACK_TYPE]:
        """The tick, and the covers, the inputs and the contacts that make a shutter decide sooner."""
        watched = [s.config.cover for s in self.shutters.values()]
        watched += [s.adapter.power_entity for s in self.shutters.values() if s.adapter.power_entity]
        inputs = [e for e in self._input_entities() if e]
        contacts = [e for s in self.shutters.values() for e in s.contacts if e]
        return [
            async_track_time_interval(self.hass, self._on_tick, timedelta(seconds=TICK_SECONDS)),
            async_track_state_change_event(self.hass, watched, self._on_cover),
            async_track_state_change_event(self.hass, inputs, self._on_input),
            async_track_state_change_event(self.hass, contacts, self._on_contact),
        ]

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
        if self._settle:
            self._settle()
            self._settle = None
        if self._release:
            self._release()
            self._release = None

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

    def _temperature(self, source: str) -> float | None:
        """A temperature source in °C, whatever its unit (#64)."""
        entity_id = self.sources.get(source)
        return units.temperature(self.hass.states.get(entity_id) if entity_id else None)

    def _speed(self, source: str) -> float | None:
        """A wind source in km/h, whatever its unit (#64)."""
        entity_id = self.sources.get(source)
        return units.speed(self.hass.states.get(entity_id) if entity_id else None)

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
        outdoor = self._temperature(CONF_OUTDOOR)
        storm = self.storm.update(
            self._speed(CONF_WIND_SPEED),
            self._speed(CONF_WIND_GUST),
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
            forecast_max=self.forecast_max,
            now=now,
            storm=storm,
            frost=frost,
            sun=sun,
            sunny=sunny,
            sun_factor=self.sunny.factor,
            outdoor=outdoor,
            pv_power=value if self.sun_source == "pv" else None,
            wind=self._speed(CONF_WIND_SPEED),
            gust=self._speed(CONF_WIND_GUST),
        )

    async def async_record_horizon(self, controller: ShutterController) -> None:
        """Store where the sun leaves this window now as a horizon point, without a reload (#54)."""
        sun = self.inputs.sun
        if sun is None or sun.elevation <= 0:
            raise HomeAssistantError("The sun is down: there is nothing to record")
        horizon = controller.horizon_with(sun)
        controller.set_horizon(horizon)
        self._quiet_update = True  # the update listener reloads on every change; this one is applied
        self.hass.config_entries.async_update_subentry(
            self.entry, self.entry.subentries[controller.id], data=dict(controller.subentry_data)
        )
        await self.async_tick()

    def quiet_update(self) -> bool:
        """Whether the last change was applied already and needs no reload (and forget it)."""
        quiet, self._quiet_update = self._quiet_update, False
        return quiet

    async def async_tick(self) -> None:
        self.inputs = self.read_inputs()
        for controller in self.shutters.values():
            await controller.async_evaluate(
                self.inputs, weather=self.weather_state, paused=not self.automatic_all
            )
            await controller.async_check_arrival()
        self._schedule_release()
        self.async_set_updated_data(None)

    def _schedule_release(self) -> None:
        """One more evaluation when the hold of a closed contact ends (#49)."""
        times = [t for c in self.shutters.values() if (t := c.guard.release_at()) is not None]
        if self._release:
            self._release()
            self._release = None
        if not times:
            return

        async def _run(_now: datetime) -> None:
            self._release = None
            await self.async_tick()

        self._release = async_call_later(self.hass, max(0.0, min(times) - time.time()) + 0.5, _run)

    async def _on_tick(self, _now: datetime) -> None:
        await self.async_tick()

    @property
    def forecast_max(self) -> float | None:
        return self.forecast.value

    @property
    def hot_day(self) -> bool:
        limit, value = self.sun_settings().hot_day, self.forecast_max
        return value is not None and limit is not None and value >= limit

    def diagnostics(self) -> dict:
        """The base controller's runtime state for the diagnostics file: what its entities show."""
        sun = self.inputs.sun
        days = {day for cell in self.sunny.reference.cells.values() for day in cell}
        return {
            "paused": not self.automatic_all,
            "sun": {
                "elevation": None if sun is None else round(sun.elevation, 1),
                "azimuth": None if sun is None else round(sun.azimuth, 1),
                "source": self.sunny.source,
                "factor": self.sunny.factor,
                "sunny": self.sunny.sunny,
            },
            "weather": {
                "outdoor": self.inputs.outdoor,
                "wind": self.inputs.wind,
                "storm": self.storm.active,
                "frost": self.frost.active,
                "forecast_max": self.forecast_max,
                "winter": self.winter.active,
                "hot_day": self.hot_day,
            },
            "clear_sky_reference": {"cells": len(self.sunny.reference.cells), "days": len(days)},
        }

    def set_winter_mode(self, mode: str) -> None:
        self.winter.mode = mode
        self.store.set_global("winter_mode", mode, setting=True)

    def set_automatic_all(self, on: bool) -> None:
        """Off: no shutter moves by itself, not even in a storm (#53); on: all go to their wanted position."""
        self.automatic_all = on
        self.store.set_global("automatic_all", on, setting=True)
        if on:
            for controller in self.shutters.values():
                controller.last_target = None

    @callback
    def _on_manual(self) -> None:
        """A manual move during a storm is put back at once, not at the next minute."""
        if not self.storm.active or self._quick:
            return

        async def _run(_now: datetime) -> None:
            self._quick = None
            await self.async_tick()

        self._quick = async_call_later(self.hass, 3, _run)

    def _check_arrival_later(self, wait: float) -> None:
        """A motor stopped short of its target: judge it once the settle time is over (#108)."""
        if self._settle:
            self._settle()

        async def _run(_now: datetime) -> None:
            self._settle = None
            for controller in self.shutters.values():
                await controller.async_check_arrival()
            waits = [w for c in self.shutters.values() if (w := c.detector.settling(time.time()))]
            if waits:  # another shutter stopped later
                self._check_arrival_later(min(waits))

        self._settle = async_call_later(self.hass, wait + 0.1, _run)

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
                if controller.arrival.active:  # the motor stopped or the module reported (#48)
                    self.hass.async_create_task(controller.async_check_arrival())
                    if wait := controller.detector.settling(time.time()):
                        self._check_arrival_later(wait)
        self.async_update_listeners()  # positions shown by our entities

    @callback
    def _on_contact(self, _event: Event[EventStateChangedData]) -> None:
        """A door or window opened or closed: decide at once, a locked-out person cannot wait (#49)."""
        self.hass.async_create_task(self.async_tick())

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
