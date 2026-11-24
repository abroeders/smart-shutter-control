"""The calibration steps of the shutter's subentry flow."""

from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    SubentryFlowResult,
)
from homeassistant.helpers import selector

from .assistant import LIFT_STEP, Action, CalibrationSession
from .const import (
    CONF_CALIBRATION,
    CONF_TRAVEL_TIME,
)
from .core import calibration_table
from .core.calibration import RollerCalibration
from .core.model import Direction
from .flow_common import (
    _number,
    _shown_form,
    _with_defaults,
)
from .units import length_unit

# labels of the calibration table's columns (the object selector's fields have no translation keys)
TABLE_LABELS = {
    "en": {"module": "Module position", "up": "Going up: opening", "down": "Going down: opening"},
    "nl": {"module": "Modulestand", "up": "Omhoog: opening", "down": "Omlaag: opening"},
}


def _review(summary: dict) -> dict[str, str]:
    """The result of a calibration: the module position for 50 % per direction, and their difference."""
    arrows = {"up": "↑", "down": "↓"}
    lines = [
        f"{arrows[d]} {s['module_at_50']} % ({s['model']}, ± {s['residual']} %)" for d, s in summary.items()
    ]
    at50 = [s["module_at_50"] for s in summary.values()]
    return {
        "summary": " · ".join(lines) or "–",
        "difference": str(abs(at50[0] - at50[1])) if len(at50) == 2 else "–",
    }


class CalibrationSteps:
    """The calibration steps (assistant and table) of the shutter's reconfigure flow."""

    _session: CalibrationSession | None = None
    _task: asyncio.Task | None = None
    _action: Action | None = None
    _shown: str | None = None  # the form on screen: input for another form (after a progress step) is ignored

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
        """Two ways (#40): the assistant that moves the shutter, or editing the measured points."""
        return self.async_show_menu(step_id="calibrate", menu_options=["cal_assistant", "cal_table"])

    async def async_step_cal_assistant(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        controller = self._controller()
        if controller is None:
            return self.async_abort(reason="not_loaded")
        if controller.storm:
            return self.async_abort(reason="storm")  # calibrating moves to intermediate positions
        if user_input is not None:
            height = length_unit(self.hass, "cm").stored(user_input.get("window_height_cm") or None)
            travel = self._get_reconfigure_subentry().data.get(CONF_TRAVEL_TIME)
            self._start(CalibrationSession.full(controller, height, float(travel) if travel else None))
            return await self.async_step_cal_next()
        height_field = {vol.Optional("window_height_cm"): _number(10, 500, 1, "cm")}
        return self.async_show_form(
            step_id="cal_assistant", data_schema=_shown_form(self.hass, height_field, {})
        )

    # --- calibration table (#40) --------------------------------------------------------------------
    _table: dict[str, Any] | None = None  # the calibration from the table, waiting for the review

    def _table_schema(self) -> dict:
        labels = TABLE_LABELS.get((self.hass.config.language or "en")[:2], TABLE_LABELS["en"])
        percent = {"number": {"min": 0, "max": 100, "step": 1, "mode": "box", "unit_of_measurement": "%"}}
        rows = selector.ObjectSelector(
            selector.ObjectSelectorConfig(
                multiple=True,
                label_field="module",
                fields={
                    "module": {"label": labels["module"], "required": True, "selector": percent},
                    "up": {"label": labels["up"], "required": False, "selector": percent},
                    "down": {"label": labels["down"], "required": False, "selector": percent},
                },
            )
        )
        return {
            vol.Required("rows"): rows,
            vol.Optional("slit_up"): _number(0, 99, 1, "%"),
            vol.Optional("slit_down"): _number(0, 99, 1, "%"),
        }

    async def async_step_cal_table(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        stored = dict(self._get_reconfigure_subentry().data.get(CONF_CALIBRATION) or {})
        errors: dict[str, str] = {}
        if user_input is not None:
            rows = [r for r in user_input.get("rows") or [] if isinstance(r, dict)]
            problems = calibration_table.check(rows)
            if problems:
                errors["base"] = problems[0]
            else:
                slits = {"up": user_input.get("slit_up"), "down": user_input.get("slit_down")}
                self._table = calibration_table.data_from(rows, slits, stored.get("window_height_cm"))
                return await self.async_step_cal_table_review()
        slits = calibration_table.slits_from(stored)
        values = {
            "rows": calibration_table.rows_from(stored),
            **{f"slit_{d}": v for d, v in slits.items()},
            **(user_input or {}),
        }
        return self.async_show_form(
            step_id="cal_table", data_schema=_with_defaults(self._table_schema(), values), errors=errors
        )

    async def async_step_cal_table_review(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        if user_input is not None and self._shown == "cal_table_review":
            return self.async_update_and_abort(
                self._get_entry(),
                self._get_reconfigure_subentry(),
                data_updates={CONF_CALIBRATION: self._table},
            )
        calibration = RollerCalibration.from_data(self._table)
        summary = calibration.summary() if isinstance(calibration, RollerCalibration) else {}
        self._shown = "cal_table_review"
        return self.async_show_form(
            step_id="cal_table_review", data_schema=vol.Schema({}), description_placeholders=_review(summary)
        )

    async def async_step_add_point(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        controller = self._controller()
        if controller is None:
            return self.async_abort(reason="not_loaded")
        if controller.storm:
            return self.async_abort(reason="storm")
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
        length = length_unit(self.hass, "cm", 0.25)
        if user_input and self._shown == "cal_measure":
            self._shown = None
            opening = float(user_input["opening"])
            session.add_point(action, length.to_stored(opening) if session.height_cm else opening)
            return await self.async_step_cal_next()
        if session.height_cm:  # in the user's length unit (#71)
            config = length.selector_config(0, session.height_cm, 0.5)
            unit = config["unit_of_measurement"]
            field = _number(config["min"], config["max"], config["step"], unit)
        else:
            unit = "%"
            field = _number(0, 100, 0.5, unit)
        self._shown = "cal_measure"
        schema = vol.Schema({vol.Required("opening"): field})
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
        return self.async_show_form(
            step_id="cal_review", data_schema=vol.Schema({}), description_placeholders=_review(summary)
        )
