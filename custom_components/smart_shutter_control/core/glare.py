"""Glare protection (#36): lower a shutter while bright sun shines on its window, whatever the temperature."""

from __future__ import annotations

from collections.abc import Callable

from .heat import Phase, SunSettings
from .model import Decision, Kind, Reason, ShutterContext
from .schedule import Phase as DayPhase
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
        self.day_phase = day_phase
        self.phase = Phase.OPEN
        self.since = 0.0
        self.started = False  # the first evaluation after a (re)start acts without the close delay

    def _go(self, phase: Phase, now: float) -> None:
        if phase is not self.phase:
            self.phase, self.since = phase, now

    def _bright(self, ctx: ShutterContext, active: bool) -> bool:
        factor = ctx.inputs.sun_factor
        if factor is None:  # no sun source, or no usable reference: the base controller's sunny decides
            return ctx.inputs.sunny
        limit = ctx.glare_from - HYSTERESIS if active else ctx.glare_from
        return factor >= limit

    def propose(self, ctx: ShutterContext) -> Decision | None:
        sun, now = ctx.inputs.sun, ctx.inputs.now
        if not ctx.glare_protection or sun is None:
            self.phase = Phase.OPEN
            self.why = ("off", {}) if not ctx.glare_protection else ("night", {})
            return None
        cfg = ctx.config
        window = WindowGeometry(cfg.azimuth, cfg.tilt, cfg.min_elevation, cfg.max_elevation, cfg.horizon)
        sun_on = window.sun_on(sun, self.settings.max_incidence)
        active = self.phase in (Phase.SHADING, Phase.LEAVING)
        day = self.day_phase(now) is DayPhase.DAY
        wanted = sun_on and day and self._bright(ctx, active)
        if self.phase is Phase.OPEN and wanted:
            # after a restart the conditions held already: no need to wait (and to open meanwhile)
            self._go(Phase.SHADING if not self.started else Phase.PENDING, now)
        self.started = True
        if self.phase is Phase.PENDING:
            if not wanted:
                self._go(Phase.OPEN, now)
            elif now - self.since >= self.settings.close_delay:
                self._go(Phase.SHADING, now)
        if self.phase is Phase.SHADING and not wanted:
            self._go(Phase.LEAVING, now)
        if self.phase is Phase.LEAVING:
            if wanted:
                self._go(Phase.SHADING, now)
            elif not sun_on or not day or now - self.since >= self.settings.open_delay:
                self._go(Phase.OPEN, now)
        self.why = self._why(ctx, window, sun, day, self.phase in (Phase.SHADING, Phase.LEAVING), now)
        if self.phase in (Phase.SHADING, Phase.LEAVING):
            return Decision(ctx.glare_position, Reason.GLARE, Kind.CAP)
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
            return "waiting", {"seconds": round(self.settings.close_delay - (now - self.since)), **bright}
        if self.phase is Phase.LEAVING:
            return "leaving", {"seconds": round(self.settings.open_delay - (now - self.since)), **bright}
        if self.phase is Phase.SHADING:
            return ("bright", bright) if bright else None
        if not day:
            return "not_day", {}
        off = window.why_not(sun, self.settings.max_incidence)
        if off:
            return off
        return "not_bright", bright
