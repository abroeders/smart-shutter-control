"""Weather and safety (#6): storm and frost detection, and the rules that act on them."""

from __future__ import annotations

from dataclasses import dataclass

from .model import Decision, Reason, ShutterContext


def cloud_coverage(attributes: dict) -> float | None:
    """The weather entity's cloud coverage in %, or None when it has none (for the view in the card, #34)."""
    try:
        value = float(attributes["cloud_coverage"])
    except (KeyError, TypeError, ValueError):
        return None
    return max(0.0, min(100.0, value))


@dataclass
class StormDetector:
    """Storm while any source is at or above its own limit, until `release` seconds after the last time."""

    wind_limit: float | None = 50.0
    gust_limit: float | None = 60.0
    release: float = 900.0
    active: bool = False
    since: float | None = None
    last_exceed: float | None = None
    source: str | None = None
    value: float | None = None

    def update(self, wind: float | None, gust: float | None, now: float) -> bool:
        exceeded = None
        if gust is not None and self.gust_limit is not None and gust >= self.gust_limit:
            exceeded = ("gust", gust)
        elif wind is not None and self.wind_limit is not None and wind >= self.wind_limit:
            exceeded = ("wind", wind)
        if exceeded is not None:
            if not self.active:
                self.active, self.since = True, now
            self.last_exceed = now
            self.source, self.value = exceeded
        elif self.active and self.last_exceed is not None and now - self.last_exceed >= self.release:
            self.active, self.since, self.source, self.value = False, None, None, None
        return self.active

    @property
    def until(self) -> float | None:
        return None if not self.active or self.last_exceed is None else self.last_exceed + self.release


@dataclass
class FrostDetector:
    """Frost at or below the limit, until `release` seconds after the temperature rose above it."""

    limit: float = 0.0
    release: float = 3600.0
    active: bool = False
    since: float | None = None
    above_since: float | None = None

    def update(self, outdoor: float | None, now: float) -> bool:
        if outdoor is None:
            return self.active  # unknown: keep the state
        if outdoor <= self.limit:
            if not self.active:
                self.active, self.since = True, now
            self.above_since = None
        elif self.active:
            self.above_since = self.above_since or now
            if now - self.above_since >= self.release:
                self.active, self.since, self.above_since = False, None, None
        return self.active


def storm_target(position: int | None, mode: str, max_position: int, wanted: int | None = None) -> int:
    """Fully open or fully closed: the end nearest to what the other rules want now (e.g. closed when the
    evening starts), else nearest to the current position; or always open / always closed. A shutter whose
    maximum position is below 100 % closes."""
    if max_position < 100 or mode == "closed":
        return 0
    if mode == "open":
        return 100
    base = wanted if wanted is not None else position
    return 100 if (base if base is not None else 0) >= 50 else 0


class StormRule:
    priority = 10

    def __init__(self, mode_of, wanted_of=None) -> None:
        self.mode_of = mode_of  # callable() -> nearest | open | closed
        self.wanted_of = wanted_of  # callable(ctx) -> the position the other rules want, or None

    def propose(self, ctx: ShutterContext) -> Decision | None:
        if not ctx.inputs.storm:
            return None
        wanted = self.wanted_of(ctx) if self.wanted_of else None
        target = storm_target(ctx.position, self.mode_of(), ctx.max_position, wanted)
        return Decision(target, Reason.STORM, final=True)


class FrostRule:
    """During frost the controller does not move the shutter (it may be frozen to the frame)."""

    priority = 11

    def propose(self, ctx: ShutterContext) -> Decision | None:
        if not ctx.inputs.frost:
            return None
        return Decision(None, Reason.FROST, final=True)


HYSTERESIS = 1.0  # °C


class TemperatureLimitRule:
    """Close above a high or below a low outdoor temperature (both optional), with a hysteresis."""

    priority = 15

    def __init__(self, close_above: float | None, close_below: float | None) -> None:
        self.close_above = close_above
        self.close_below = close_below
        self.state: str | None = None  # heat_limit, cold_limit or None

    def propose(self, ctx: ShutterContext) -> Decision | None:
        t = ctx.inputs.outdoor
        if t is not None:
            above, below = self.close_above, self.close_below
            if above is not None and (
                t > above or (self.state == Reason.HEAT_LIMIT and t > above - HYSTERESIS)
            ):
                self.state = Reason.HEAT_LIMIT
            elif below is not None and (
                t < below or (self.state == Reason.COLD_LIMIT and t < below + HYSTERESIS)
            ):
                self.state = Reason.COLD_LIMIT
            else:
                self.state = None
        if self.state is None:
            return None
        return Decision(0, self.state, final=True)
