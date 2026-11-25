"""Heat protection: lower a shutter to its shading position while the sun shines on its window (#3)."""

from __future__ import annotations

from dataclasses import dataclass

from .model import Decision, Kind, Reason, ShutterContext
from .protection import Phase, ProtectionState
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
    away_offset: float = 3.0  # °C: both heat limits are this much lower while nobody is home (#51)


class HeatProtectionRule:
    """A cap: at most the shading position while the sun is on the window, it is sunny and warm."""

    priority = PRIORITY
    name = "heat"

    def __init__(self, settings: SunSettings) -> None:
        self.settings = settings
        self.why: tuple[str, dict] | None = None  # (#56)
        self.shade = DepthShading()  # the position from the sun with a room geometry (#55)
        self.state = ProtectionState()
        self.incidence: float | None = None
        self.sun_on: bool = False

    def _hot_day(self, ctx: ShutterContext) -> bool:
        forecast, limit = ctx.inputs.forecast_max, self.settings.hot_day
        return forecast is not None and limit is not None and forecast >= limit

    def limits(self, ctx: ShutterContext) -> tuple[float, float]:
        """The outdoor and the room limit in use: lower while away (#51)."""
        lower = self.settings.away_offset if ctx.inputs.away else 0.0
        return self.settings.heat_outdoor - lower, self.settings.heat_room - lower

    def _warm(self, ctx: ShutterContext) -> bool:
        if self._hot_day(ctx):
            return True
        outdoor, room = ctx.inputs.outdoor, ctx.room
        if outdoor is None and room is None:
            return True
        outdoor_limit, room_limit = self.limits(ctx)
        return (outdoor is not None and outdoor >= outdoor_limit) or (room is not None and room >= room_limit)

    @property
    def phase(self) -> Phase:
        return self.state.phase

    def propose(self, ctx: ShutterContext) -> Decision | None:
        sun, now = ctx.inputs.sun, ctx.inputs.now
        if not ctx.heat_protection or sun is None:
            self.state.reset()
            self.sun_on, self.incidence = False, None
            self.why = ("off", {}) if not ctx.heat_protection else ("night", {})
            return None
        cfg = ctx.config
        window = WindowGeometry(cfg.azimuth, cfg.tilt, cfg.min_elevation, cfg.max_elevation, cfg.horizon)
        self.incidence = window.incidence(sun)
        self.sun_on = window.sun_on(sun, self.settings.max_incidence)
        wanted = self.sun_on and ctx.inputs.sunny and self._warm(ctx)
        s = self.settings
        self.state.step(wanted, not self.sun_on, now, s.close_delay, s.open_delay)
        self.why = self._why(ctx, window, sun, now)
        if self.state.active:
            position = self.shade(now, cfg.room, sun, cfg.azimuth, cfg.tilt, ctx.shading_position)
            return Decision(position, Reason.SUN, Kind.CAP)
        self.shade.reset()
        return None

    def _why(self, ctx: ShutterContext, window: WindowGeometry, sun, now: float) -> tuple[str, dict] | None:
        if self.phase is Phase.PENDING:
            return "waiting", {"seconds": self.state.remaining(now, self.settings.close_delay)}
        if self.phase is Phase.LEAVING:
            return "leaving", {"seconds": self.state.remaining(now, self.settings.open_delay)}
        if self.phase is Phase.SHADING:
            return None
        off = window.why_not(sun, self.settings.max_incidence)
        if off:
            return off
        if not ctx.inputs.sunny:
            return "not_sunny", {}
        outdoor_limit, room_limit = self.limits(ctx)
        values: dict = {"outdoor": ctx.inputs.outdoor, "limit": outdoor_limit}
        if ctx.room is not None:
            values |= {"room": ctx.room, "room_limit": room_limit}
        if ctx.inputs.away:
            values |= {"away": True}
        if ctx.inputs.forecast_max is not None and self.settings.hot_day is not None:
            values |= {"forecast": ctx.inputs.forecast_max, "forecast_limit": self.settings.hot_day}
        return "too_cold", values
