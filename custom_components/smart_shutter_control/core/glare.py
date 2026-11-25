"""Glare protection (#36): lower a shutter while bright sun shines on its window, whatever the temperature."""

from __future__ import annotations

from collections.abc import Callable

from .heat import SunSettings
from .model import Decision, Kind, Reason, ShutterContext
from .protection import Phase, ProtectionState
from .schedule import Phase as DayPhase
from .shading import DepthShading
from .sun import WindowGeometry

PRIORITY = 41
HYSTERESIS = 0.15  # share of the clear-sky value: once active, it stays until this far below the limit


class GlareProtectionRule:
    """A cap: at most the glare position while the sun is on the window and bright, during the day phase.

    Uses the largest angle of incidence and the delays of heat protection (`SunSettings`).
    """

    priority = PRIORITY
    name = "glare"

    def __init__(self, settings: SunSettings, day_phase: Callable[[float], DayPhase]) -> None:
        self.settings = settings
        self.why: tuple[str, dict] | None = None  # (#56)
        self.shade = DepthShading()  # the position from the sun with a room geometry (#55)
        self.day_phase = day_phase
        self.state = ProtectionState()

    @property
    def phase(self) -> Phase:
        return self.state.phase

    def _bright(self, ctx: ShutterContext, active: bool) -> bool:
        factor = ctx.inputs.sun_factor
        if factor is None:  # no sun source, or no usable reference: the base controller's sunny decides
            return ctx.inputs.sunny
        limit = ctx.glare_from - HYSTERESIS if active else ctx.glare_from
        return factor >= limit

    def propose(self, ctx: ShutterContext) -> Decision | None:
        sun, now = ctx.inputs.sun, ctx.inputs.now
        if not ctx.glare_protection or sun is None:
            self.state.reset()
            self.why = ("off", {}) if not ctx.glare_protection else ("night", {})
            return None
        cfg = ctx.config
        window = WindowGeometry(cfg.azimuth, cfg.tilt, cfg.min_elevation, cfg.max_elevation, cfg.horizon)
        sun_on = window.sun_on(sun, self.settings.max_incidence)
        day = self.day_phase(now) is DayPhase.DAY
        away = ctx.inputs.away  # nobody to dazzle (#51): ends through the open delay
        wanted = sun_on and day and not away and self._bright(ctx, self.state.active)
        s = self.settings
        self.state.step(wanted, not sun_on or not day, now, s.close_delay, s.open_delay)
        self.why = self._why(ctx, window, sun, day, self.state.active, now)
        if self.state.active:
            position = self.shade(now, cfg.room, sun, cfg.azimuth, cfg.tilt, ctx.glare_position)
            return Decision(position, Reason.GLARE, Kind.CAP)
        self.shade.reset()
        return None

    def _why(self, ctx, window: WindowGeometry, sun, day: bool, active: bool, now: float):
        factor = ctx.inputs.sun_factor
        bright = (
            {
                "factor": round(100 * factor),
                "limit": round(100 * (ctx.glare_from - (HYSTERESIS if active else 0))),
            }
            if factor is not None
            else {}
        )
        if self.phase is Phase.PENDING:
            return "waiting", {"seconds": self.state.remaining(now, self.settings.close_delay), **bright}
        if self.phase is Phase.LEAVING:
            return "leaving", {"seconds": self.state.remaining(now, self.settings.open_delay), **bright}
        if self.phase is Phase.SHADING:
            return ("bright", bright) if bright else None
        if ctx.inputs.away:
            return "away", {}
        if not day:
            return "not_day", {}
        off = window.why_not(sun, self.settings.max_incidence)
        if off:
            return off
        return "not_bright", bright
