"""Heat protection: lower a shutter to its shading position while the sun shines on its window (#3)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .model import Decision, Kind, Reason, ShutterContext
from .sun import WindowGeometry

PRIORITY = 40


@dataclass(frozen=True)
class SunSettings:
    max_incidence: float = 85.0
    heat_outdoor: float = 22.0
    heat_room: float = 24.0
    close_delay: float = 300.0  # s
    open_delay: float = 1200.0  # s


class Phase(StrEnum):
    OPEN = "open"
    PENDING = "pending"  # conditions met, waiting for close_delay
    SHADING = "shading"
    LEAVING = "leaving"  # conditions gone, waiting for open_delay


class HeatProtectionRule:
    """A cap: at most the shading position while the sun is on the window, it is sunny and warm."""

    priority = PRIORITY

    def __init__(self, settings: SunSettings) -> None:
        self.settings = settings
        self.phase = Phase.OPEN
        self.since = 0.0
        self.incidence: float | None = None
        self.sun_on: bool = False

    def _warm(self, ctx: ShutterContext) -> bool:
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
            return None
        cfg = ctx.config
        window = WindowGeometry(cfg.azimuth, cfg.tilt, cfg.min_elevation, cfg.max_elevation)
        self.incidence = window.incidence(sun)
        self.sun_on = window.sun_on(sun, self.settings.max_incidence)
        wanted = self.sun_on and ctx.inputs.sunny and self._warm(ctx)
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
            elif not self.sun_on or now - self.since >= self.settings.open_delay:
                self._go(Phase.OPEN, now)
        if self.phase in (Phase.SHADING, Phase.LEAVING):
            return Decision(ctx.shading_position, Reason.SUN, Kind.CAP)
        return None
