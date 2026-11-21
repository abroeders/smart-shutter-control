"""Heat protection: lower a shutter to its shading position while the sun shines on its window (#3)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .model import Decision, Kind, Reason, ShutterContext
from .shading import DepthShading
from .sun import WindowGeometry

PRIORITY = 40


@dataclass(frozen=True)
class SunSettings:
    max_incidence: float = 85.0
    heat_outdoor: float = 22.0
    heat_room: float = 24.0
    close_delay: float = 300.0  # s
    open_delay: float = 1200.0  # s
    hot_day: float | None = 28.0  # °C forecast maximum from which the temperature limits do not apply (#50)


class Phase(StrEnum):
    OPEN = "open"
    PENDING = "pending"  # conditions met, waiting for close_delay
    SHADING = "shading"
    LEAVING = "leaving"  # conditions gone, waiting for open_delay


class HeatProtectionRule:
    """A cap: at most the shading position while the sun is on the window, it is sunny and warm."""

    priority = PRIORITY
    name = "heat"

    def __init__(self, settings: SunSettings) -> None:
        self.settings = settings
        self.why: tuple[str, dict] | None = None  # (#56)
        self.shade = DepthShading()  # the position from the sun with a room geometry (#55)
        self.phase = Phase.OPEN
        self.since = 0.0
        self.started = False  # the first evaluation after a (re)start acts without the close delay
        self.incidence: float | None = None
        self.sun_on: bool = False

    def _hot_day(self, ctx: ShutterContext) -> bool:
        forecast, limit = ctx.inputs.forecast_max, self.settings.hot_day
        return forecast is not None and limit is not None and forecast >= limit

    def _warm(self, ctx: ShutterContext) -> bool:
        if self._hot_day(ctx):
            return True
        outdoor, room = ctx.inputs.outdoor, ctx.room
        if outdoor is None and room is None:
            return True
        return (outdoor is not None and outdoor >= self.settings.heat_outdoor) or (
            room is not None and room >= self.settings.heat_room
        )

    def _go(self, phase: Phase, now: float) -> None:
        if phase is not self.phase:
            self.phase, self.since = phase, now

    def propose(self, ctx: ShutterContext) -> Decision | None:
        sun, now = ctx.inputs.sun, ctx.inputs.now
        if not ctx.heat_protection or sun is None:
            self.phase, self.sun_on, self.incidence = Phase.OPEN, False, None
            self.why = ("off", {}) if not ctx.heat_protection else ("night", {})
            return None
        cfg = ctx.config
        window = WindowGeometry(cfg.azimuth, cfg.tilt, cfg.min_elevation, cfg.max_elevation, cfg.horizon)
        self.incidence = window.incidence(sun)
        self.sun_on = window.sun_on(sun, self.settings.max_incidence)
        wanted = self.sun_on and ctx.inputs.sunny and self._warm(ctx)
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
            elif not self.sun_on or now - self.since >= self.settings.open_delay:
                self._go(Phase.OPEN, now)
        self.why = self._why(ctx, window, sun, now)
        if self.phase in (Phase.SHADING, Phase.LEAVING):
            position = self.shade(now, cfg.room, sun, cfg.azimuth, cfg.tilt, ctx.shading_position)
            return Decision(position, Reason.SUN, Kind.CAP)
        self.shade.reset()
        return None

    def _why(self, ctx: ShutterContext, window: WindowGeometry, sun, now: float) -> tuple[str, dict] | None:
        if self.phase is Phase.PENDING:
            return "waiting", {"seconds": round(self.settings.close_delay - (now - self.since))}
        if self.phase is Phase.LEAVING:
            return "leaving", {"seconds": round(self.settings.open_delay - (now - self.since))}
        if self.phase is Phase.SHADING:
            return None
        off = window.why_not(sun, self.settings.max_incidence)
        if off:
            return off
        if not ctx.inputs.sunny:
            return "not_sunny", {}
        values = {"outdoor": ctx.inputs.outdoor, "limit": self.settings.heat_outdoor}
        if ctx.room is not None:
            values |= {"room": ctx.room, "room_limit": self.settings.heat_room}
        if ctx.inputs.forecast_max is not None and self.settings.hot_day is not None:
            values |= {"forecast": ctx.inputs.forecast_max, "forecast_limit": self.settings.hot_day}
        return "too_cold", values
