"""Config flow (base controller), options flow and the subentry flow for a shutter."""

from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol
from homeassistant.components.cover import CoverEntityFeature
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.const import ATTR_SUPPORTED_FEATURES, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .assistant import LIFT_STEP, Action, CalibrationSession
from .const import (
    CONF_AZIMUTH,
    CONF_CALIBRATION,
    CONF_COVER,
    CONF_HEAT_OUTDOOR,
    CONF_HEAT_PROTECTION,
    CONF_HEAT_ROOM,
    CONF_MAX_ELEVATION,
    CONF_MAX_POSITION,
    CONF_MIN_ELEVATION,
    CONF_MOTOR_POWER,
    CONF_OUTDOOR,
    CONF_PV_FORECAST,
    CONF_PV_PEAK,
    CONF_PV_POWER,
    CONF_ROOM_TEMPERATURE,
    CONF_SCHEDULE,
    CONF_SHADING_POSITION,
    CONF_TILT,
    CONF_TRAVEL_TIME,
    CONF_WEATHER,
    CONF_WIND_GUST,
    CONF_WIND_SPEED,
    DEFAULT_NAME,
    DEFAULT_OPTIONS,
    DEFAULT_SHUTTER,
    DOMAIN,
    OPT_CLOSE_DELAY,
    OPT_HEAT_OUTDOOR,
    OPT_HEAT_ROOM,
    OPT_HOLIDAY_CALENDAR,
    OPT_HOLIDAYS_EXCLUDED,
    OPT_HOLIDAYS_EXTRA,
    OPT_MAX_INCIDENCE,
    OPT_OPEN_DELAY,
    OPT_SCHEDULE,
    OPT_STORM_LIMIT,
    OPT_SUNNY_THRESHOLD,
    OPT_WEEKEND_DAYS,
    SUBENTRY_SHUTTER,
)
from .core.model import Direction
from .core.schedule import DEFAULT_SCHEDULE, HolidayCalendar, merged, parse_holidays, weekend_set


def _sensor(device_class: str | None = None, multiple: bool = False) -> selector.EntitySelector:
    config: dict[str, Any] = {"domain": "sensor", "multiple": multiple}
    if device_class:
        config["device_class"] = device_class
    return selector.EntitySelector(selector.EntitySelectorConfig(**config))


def _number(low: float, high: float, step: float, unit: str | None = None) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=low, max=high, step=step, unit_of_measurement=unit, mode=selector.NumberSelectorMode.BOX
        )
    )


def _with_defaults(schema: dict, values: dict[str, Any]) -> vol.Schema:
    """Fill the defaults of a schema from the current values (optional keys get a suggested value)."""
    out = {}
    for key, validator in schema.items():
        name = str(key)
        if name in values and values[name] is not None:
            if isinstance(key, vol.Required):
                key = vol.Required(name, default=values[name])
            else:
                key = vol.Optional(name, description={"suggested_value": values[name]})
        out[key] = validator
    return vol.Schema(out)


def _time() -> selector.TimeSelector:
    return selector.TimeSelector()


def _phase_switch(base: bool) -> selector.Selector:
    """On/off in the base schedule; inherit/on/off for a shutter."""
    if base:
        return selector.BooleanSelector()
    return selector.SelectSelector(
        selector.SelectSelectorConfig(options=["inherit", "on", "off"], translation_key="phase_switch")
    )


def schedule_fields(base: bool) -> dict:
    """The schedule settings; for a shutter every field is optional (empty = the base value)."""
    key = vol.Required if base else vol.Optional
    return {
        key("weekday_slit"): _time(),
        key("weekday_open"): _time(),
        key("weekend_slit"): _time(),
        key("weekend_open"): _time(),
        key("slit_phase"): _phase_switch(base),
        key("not_before_sunrise"): _phase_switch(base),
        key("sunrise_offset"): _number(-120, 120, 5, "min"),
        key("dusk_phase"): _phase_switch(base),
        key("dusk_offset"): _number(-120, 120, 5, "min"),
        key("dusk_position"): _number(0, 100, 5, "%"),
        key("close_offset"): _number(-120, 180, 5, "min"),
        vol.Optional("close_earliest"): _time(),
        vol.Optional("close_latest"): _time(),
        key("open_position"): _number(0, 100, 5, "%"),
        key("slit_module"): _number(0, 60, 1, "%"),
        key("sleep_in_until"): _time(),
        key("manual_mode"): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=["until_next_phase", "for_duration", "ignore"], translation_key="manual_mode"
            )
        ),
        key("manual_duration"): _number(5, 1440, 5, "min"),
    }


SOURCES = {
    vol.Required(CONF_OUTDOOR): _sensor("temperature"),
    vol.Optional(CONF_WEATHER): selector.EntitySelector(selector.EntitySelectorConfig(domain="weather")),
    vol.Optional(CONF_PV_POWER): _sensor("power", multiple=True),
    vol.Optional(CONF_PV_PEAK): _number(0.1, 100, 0.1, "kWp"),
    vol.Optional(CONF_PV_FORECAST): _sensor("power"),
    vol.Optional(CONF_WIND_SPEED): _sensor("wind_speed"),
    vol.Optional(CONF_WIND_GUST): _sensor("wind_speed"),
}


class SmartShutterControlConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._name = DEFAULT_NAME

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._name = user_input[CONF_NAME]
            return await self.async_step_sources()
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required(CONF_NAME, default=DEFAULT_NAME): str})
        )

    async def async_step_sources(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title=self._name, data=user_input, options=dict(DEFAULT_OPTIONS))
        return self.async_show_form(step_id="sources", data_schema=vol.Schema(SOURCES))

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            return self.async_update_reload_and_abort(entry, data=user_input)
        return self.async_show_form(
            step_id="reconfigure", data_schema=_with_defaults(SOURCES, dict(entry.data))
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SmartShutterControlOptionsFlow()

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        return {SUBENTRY_SHUTTER: ShutterSubentryFlow}


class SmartShutterControlOptionsFlow(OptionsFlow):
    """One page per subject; later issues add their pages to the menu."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(step_id="init", menu_options=["schedule", "holidays", "sun", "storm"])

    async def async_step_schedule(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**DEFAULT_OPTIONS, **self.config_entry.options}
        base = merged(current.get(OPT_SCHEDULE), None)
        if user_input is not None:
            schedule = {k: user_input.get(k) for k in DEFAULT_SCHEDULE}
            return self.async_create_entry(data={**current, OPT_SCHEDULE: schedule})
        return self.async_show_form(
            step_id="schedule", data_schema=_with_defaults(schedule_fields(base=True), base)
        )

    async def async_step_holidays(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**DEFAULT_OPTIONS, **self.config_entry.options}
        errors: dict[str, str] = {}
        bad: list[int] = []
        if user_input is not None:
            for key in (OPT_HOLIDAYS_EXTRA, OPT_HOLIDAYS_EXCLUDED):
                _, wrong = parse_holidays(user_input.get(key))
                if wrong:
                    errors[key] = "bad_dates"
                    bad += wrong
            if not errors:
                data = {**current, **user_input}
                for key in (OPT_HOLIDAY_CALENDAR, OPT_HOLIDAYS_EXTRA, OPT_HOLIDAYS_EXCLUDED):
                    data[key] = user_input.get(key)  # cleared fields stay cleared
                return self.async_create_entry(data=data)
        values = {OPT_WEEKEND_DAYS: ["sat", "sun"], **current, **(user_input or {})}
        schema = {
            vol.Optional(OPT_HOLIDAY_CALENDAR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="calendar")
            ),
            vol.Required(OPT_WEEKEND_DAYS): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
                    multiple=True,
                    translation_key="weekday",
                )
            ),
            vol.Optional(OPT_HOLIDAYS_EXTRA): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Optional(OPT_HOLIDAYS_EXCLUDED): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
        }
        return self.async_show_form(
            step_id="holidays",
            data_schema=_with_defaults(schema, values),
            errors=errors,
            description_placeholders={"lines": ", ".join(map(str, bad)) or "–", "list": self._holiday_list()},
        )

    def _holiday_list(self) -> str:
        """This year's holidays as the schedules see them now."""
        coordinator = getattr(self.config_entry, "runtime_data", None)
        calendar: HolidayCalendar | None = getattr(coordinator, "calendar", None)
        if calendar is None:
            opts = self.config_entry.options
            calendar = HolidayCalendar(
                weekend_set(opts.get(OPT_WEEKEND_DAYS)),
                parse_holidays(opts.get(OPT_HOLIDAYS_EXTRA))[0],
                parse_holidays(opts.get(OPT_HOLIDAYS_EXCLUDED))[0],
            )
        from homeassistant.util import dt as dt_util

        days = calendar.listing(dt_util.now().year)
        return "\n".join(f"{d.isoformat()} {name}".strip() for d, name in days) or "–"

    async def async_step_sun(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**DEFAULT_OPTIONS, **self.config_entry.options}
        if user_input is not None:
            return self.async_create_entry(data={**current, **user_input})
        schema = {
            vol.Required(OPT_SUNNY_THRESHOLD): _number(10, 100, 5, "%"),
            vol.Required(OPT_MAX_INCIDENCE): _number(30, 90, 1, "°"),
            vol.Required(OPT_HEAT_OUTDOOR): _number(-10, 40, 0.5, "°C"),
            vol.Required(OPT_HEAT_ROOM): _number(10, 35, 0.5, "°C"),
            vol.Required(OPT_CLOSE_DELAY): _number(0, 60, 1, "min"),
            vol.Required(OPT_OPEN_DELAY): _number(0, 120, 1, "min"),
        }
        return self.async_show_form(step_id="sun", data_schema=_with_defaults(schema, current))

    async def async_step_storm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**DEFAULT_OPTIONS, **self.config_entry.options}
        if user_input is not None:
            return self.async_create_entry(data={**current, **user_input})
        schema = {vol.Required(OPT_STORM_LIMIT): _number(10, 200, 1, "km/h")}
        return self.async_show_form(step_id="storm", data_schema=_with_defaults(schema, current))


SHUTTER = {
    vol.Required(CONF_COVER): selector.EntitySelector(selector.EntitySelectorConfig(domain="cover")),
    vol.Optional(CONF_NAME): str,
    vol.Required(CONF_AZIMUTH): _number(0, 359, 1, "°"),
    vol.Required(CONF_TILT): _number(0, 90, 1, "°"),
    vol.Required(CONF_MIN_ELEVATION): _number(0, 90, 1, "°"),
    vol.Required(CONF_MAX_ELEVATION): _number(0, 90, 1, "°"),
    vol.Optional(CONF_ROOM_TEMPERATURE): _sensor("temperature"),
    vol.Optional(CONF_MOTOR_POWER): _sensor("power"),
    vol.Optional(CONF_TRAVEL_TIME): _number(5, 300, 0.5, "s"),
    vol.Required(CONF_MAX_POSITION): _number(0, 100, 5, "%"),
    vol.Required(CONF_HEAT_PROTECTION): selector.BooleanSelector(),
    vol.Required(CONF_SHADING_POSITION): _number(0, 100, 5, "%"),
    vol.Optional(CONF_HEAT_OUTDOOR): _number(-10, 40, 0.5, "°C"),
    vol.Optional(CONF_HEAT_ROOM): _number(10, 35, 0.5, "°C"),
}


class ShutterSubentryFlow(ConfigSubentryFlow):
    """Add or change one shutter."""

    def _errors(self, user_input: dict[str, Any], subentry_id: str | None = None) -> dict[str, str]:
        errors: dict[str, str] = {}
        state = self.hass.states.get(user_input[CONF_COVER])
        features = int(state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)) if state else 0
        if state is not None and not features & CoverEntityFeature.SET_POSITION:
            errors[CONF_COVER] = "no_position"
        for sub in self._get_entry().subentries.values():
            if sub.subentry_id != subentry_id and sub.data.get(CONF_COVER) == user_input[CONF_COVER]:
                errors[CONF_COVER] = "already_configured"
        if user_input[CONF_MIN_ELEVATION] >= user_input[CONF_MAX_ELEVATION]:
            errors[CONF_MAX_ELEVATION] = "elevation_order"
        return errors

    def _title(self, user_input: dict[str, Any]) -> str:
        if user_input.get(CONF_NAME):
            return user_input[CONF_NAME]
        state = self.hass.states.get(user_input[CONF_COVER])
        return state.name if state else user_input[CONF_COVER]

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = self._errors(user_input)
            if not errors:
                return self.async_create_entry(
                    title=self._title(user_input), data=user_input, unique_id=user_input[CONF_COVER]
                )
        values = {**DEFAULT_SHUTTER, **(user_input or {})}
        return self.async_show_form(
            step_id="user", data_schema=_with_defaults(SHUTTER, values), errors=errors
        )

    # --- reconfigure: a menu ------------------------------------------------------------------------
    _session: CalibrationSession | None = None
    _task: asyncio.Task | None = None
    _action: Action | None = None
    _shown: str | None = None  # the form on screen: input for another form (after a progress step) is ignored

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return self.async_show_menu(
            step_id="reconfigure",
            menu_options=["settings", "schedule", "schedule_reset", "calibrate", "add_point"],
        )

    async def async_step_settings(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        subentry = self._get_reconfigure_subentry()
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = self._errors(user_input, subentry.subentry_id)
            if not errors:
                return self.async_update_and_abort(
                    self._get_entry(),
                    subentry,
                    title=self._title(user_input),
                    data_updates=user_input,
                    unique_id=user_input[CONF_COVER],
                )
        values = {**DEFAULT_SHUTTER, **dict(subentry.data), **(user_input or {})}
        return self.async_show_form(
            step_id="settings", data_schema=_with_defaults(SHUTTER, values), errors=errors
        )

    # --- schedule overrides -----------------------------------------------------------------------
    def _base_schedule(self) -> dict[str, Any]:
        return merged(self._get_entry().options.get(OPT_SCHEDULE), None)

    async def async_step_schedule(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        subentry = self._get_reconfigure_subentry()
        if user_input is not None:
            overrides = {k: v for k, v in user_input.items() if v not in (None, "", "inherit")}
            return self.async_update_and_abort(
                self._get_entry(), subentry, data_updates={CONF_SCHEDULE: overrides}
            )
        overrides = dict(subentry.data.get(CONF_SCHEDULE) or {})
        base = self._base_schedule()
        summary = ", ".join(f"{k} {v}" for k, v in base.items() if v is not None)
        return self.async_show_form(
            step_id="schedule",
            data_schema=_with_defaults(schedule_fields(base=False), overrides),
            description_placeholders={"base": summary},
        )

    async def async_step_schedule_reset(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return self.async_update_and_abort(
            self._get_entry(), self._get_reconfigure_subentry(), data_updates={CONF_SCHEDULE: {}}
        )

    # --- calibration assistant ------------------------------------------------------------------
    def _controller(self):
        entry = self._get_entry()
        coordinator = getattr(entry, "runtime_data", None)
        if coordinator is None:
            return None
        return coordinator.shutters.get(self._reconfigure_subentry_id)

    def _start(self, session: CalibrationSession) -> None:
        self._session = session
        session.controller.paused = True

    def async_remove(self) -> None:
        """The flow ends (saved or cancelled): automatic control may move the shutter again."""
        if self._task is not None and not self._task.done():
            self._task.cancel()
        if self._session is not None:
            self._session.controller.paused = False

    async def async_step_calibrate(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        controller = self._controller()
        if controller is None:
            return self.async_abort(reason="not_loaded")
        if user_input is not None:
            height = user_input.get("window_height_cm") or None
            travel = self._get_reconfigure_subentry().data.get(CONF_TRAVEL_TIME)
            self._start(CalibrationSession.full(controller, height, float(travel) if travel else None))
            return await self.async_step_cal_next()
        schema = vol.Schema({vol.Optional("window_height_cm"): _number(10, 500, 1, "cm")})
        return self.async_show_form(step_id="calibrate", data_schema=schema)

    async def async_step_add_point(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        controller = self._controller()
        if controller is None:
            return self.async_abort(reason="not_loaded")
        if user_input is not None:
            stored = dict(self._get_reconfigure_subentry().data.get(CONF_CALIBRATION) or {})
            direction = Direction(user_input["direction"])
            self._start(
                CalibrationSession.one_point(controller, stored, int(user_input["module"]), direction)
            )
            return await self.async_step_cal_next()
        schema = vol.Schema(
            {
                vol.Required("module", default=50): _number(1, 99, 1, "%"),
                vol.Required("direction", default="up"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=["up", "down"], translation_key="direction")
                ),
            }
        )
        return self.async_show_form(step_id="add_point", data_schema=schema)

    async def async_step_cal_next(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        session = self._session
        if not session.queue:
            return await self.async_step_cal_review()
        self._action = session.queue.pop(0)
        if self._action.kind == "lift":
            session.lift_at = 0
            self._action = Action("lift", 0)
        return await self.async_step_cal_move()

    async def async_step_cal_move(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        action = self._action
        if self._task is None:
            job = (
                self._session.measure_travel() if action.kind == "time" else self._session.move(action.module)
            )
            self._task = self.hass.async_create_task(job)
        if not self._task.done():
            return self.async_show_progress(
                step_id="cal_move",
                progress_action="timing" if action.kind == "time" else "moving",
                progress_task=self._task,
                description_placeholders={"position": str(action.module)},
            )
        self._task = None
        following = {"measure": "cal_measure", "lift": "cal_lift"}.get(action.kind, "cal_next")
        return self.async_show_progress_done(next_step_id=following)

    async def async_step_cal_measure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        session, action = self._session, self._action
        if user_input and self._shown == "cal_measure":
            self._shown = None
            session.add_point(action, float(user_input["opening"]))
            return await self.async_step_cal_next()
        unit = "cm" if session.height_cm else "%"
        top = session.height_cm or 100
        self._shown = "cal_measure"
        schema = vol.Schema({vol.Required("opening"): _number(0, top, 0.5, unit)})
        return self.async_show_form(
            step_id="cal_measure",
            data_schema=schema,
            description_placeholders={
                "position": str(action.module),
                "direction": "↑" if action.direction is Direction.UP else "↓",
                "unit": unit,
                "reached": "✓" if session.reached else "⚠",
            },
        )

    async def async_step_cal_lift(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        session = self._session
        if user_input and self._shown == "cal_lift":
            self._shown = None
            if session.lifted(bool(user_input["lifted"])):
                return await self.async_step_cal_next()
            session.lift_at += LIFT_STEP
            self._action = Action("lift", session.lift_at)
            return await self.async_step_cal_move()
        if session.lift_at == 0:  # first at closed: start stepping
            session.lift_at = LIFT_STEP
            self._action = Action("lift", session.lift_at)
            return await self.async_step_cal_move()
        schema = vol.Schema({vol.Required("lifted", default=False): selector.BooleanSelector()})
        self._shown = "cal_lift"
        return self.async_show_form(
            step_id="cal_lift",
            data_schema=schema,
            description_placeholders={"position": str(session.lift_at)},
        )

    async def async_step_cal_review(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        session = self._session
        summary = session.summary()
        if user_input is not None:
            session.controller.paused = False
            return self.async_update_and_abort(
                self._get_entry(),
                self._get_reconfigure_subentry(),
                data_updates=session.updates(),
            )
        arrows = {"up": "↑", "down": "↓"}
        lines = [
            f"{arrows[d]} {s['module_at_50']} % ({s['model']}, ± {s['residual']} %)"
            for d, s in summary.items()
        ]
        at50 = [s["module_at_50"] for s in summary.values()]
        return self.async_show_form(
            step_id="cal_review",
            data_schema=vol.Schema({}),
            description_placeholders={
                "summary": " · ".join(lines) or "–",
                "difference": str(abs(at50[0] - at50[1])) if len(at50) == 2 else "–",
            },
        )
