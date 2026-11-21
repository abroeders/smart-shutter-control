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

    def __init__(self, settings: SunSettings, day_phase: Callable[[float], DayPhase]) -> None:
        self.settings = settings
        self.day_phase = day_phase
        self.phase = Phase.OPEN
        self.since = 0.0

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
            return None
        cfg = ctx.config
        window = WindowGeometry(cfg.azimuth, cfg.tilt, cfg.min_elevation, cfg.max_elevation)
        sun_on = window.sun_on(sun, self.settings.max_incidence)
        active = self.phase in (Phase.SHADING, Phase.LEAVING)
        day = self.day_phase(now) is DayPhase.DAY
        wanted = sun_on and day and self._bright(ctx, active)
        if self.phase is Phase.OPEN and wanted:
            self._go(Phase.PENDING, now)
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
        if self.phase in (Phase.SHADING, Phase.LEAVING):
            return Decision(ctx.glare_position, Reason.GLARE, Kind.CAP)
        return None
