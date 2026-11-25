"""Winter mode (#7): the 24-hour mean outdoor temperature, winter detection and the winter rule."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .model import Decision, Kind, Reason, ShutterContext
from .schedule import Phase

DAY = 24 * 3600.0
HYSTERESIS = 1.0  # °C


@dataclass
class OutdoorMean:
    """Time-weighted mean of the last 24 hours: each value holds until the next one."""

    window: float = DAY
    samples: list[tuple[float, float]] = field(default_factory=list)

    def add(self, value: float | None, now: float) -> None:
        if value is None:
            return
        if self.samples and self.samples[-1][1] == value:
            return
        self.samples.append((now, value))
        start = now - self.window
        while len(self.samples) > 1 and self.samples[1][0] <= start:
            self.samples.pop(0)  # keep one sample before the window: it holds at its start

    def mean(self, now: float) -> float | None:
        if not self.samples:
            return None
        start = now - self.window
        total = weight = 0.0
        for i, (t, v) in enumerate(self.samples):
            begin = max(t, start)
            end = self.samples[i + 1][0] if i + 1 < len(self.samples) else now
            if end > begin:
                total += v * (end - begin)
                weight += end - begin
        return total / weight if weight else self.samples[-1][1]

    def to_dict(self) -> list:
        return [list(s) for s in self.samples]

    @classmethod
    def from_dict(cls, data: list | None) -> OutdoorMean:
        return cls(samples=[(float(t), float(v)) for t, v in (data or [])])


@dataclass
class WinterDetector:
    limit: float = 12.0
    mode: str = "auto"  # auto, on, off
    active: bool = False

    def update(self, mean: float | None) -> bool:
        if self.mode == "on":
            self.active = True
        elif self.mode == "off":
            self.active = False
        elif mean is not None:
            self.active = mean < (self.limit + HYSTERESIS if self.active else self.limit)
        return self.active


class WinterRule:
    """In winter: closed all day when it is very cold; the dusk position never raises a closed shutter."""

    priority = 50
    name = "winter"
    why: tuple[str, dict] | None = None

    def __init__(
        self,
        enabled: Callable[[], bool],
        closed_below: Callable[[], float | None],
        phase: Callable[[float], Phase],
        dusk_position: Callable[[], int],
    ) -> None:
        self.enabled = enabled
        self.closed_below = closed_below
        self.phase = phase
        self.dusk_position = dusk_position

    def propose(self, ctx: ShutterContext) -> Decision | None:
        if not ctx.inputs.winter or not self.enabled():
            self.why = ("off", {})
            return None
        limit, outdoor = self.closed_below(), ctx.inputs.outdoor
        if limit is not None and outdoor is not None and outdoor <= limit:
            return Decision(0, Reason.WINTER)
        if (
            self.phase(ctx.inputs.now) is Phase.DUSK
            and ctx.position is not None
            and ctx.position < self.dusk_position()
        ):
            return Decision(ctx.position, Reason.WINTER, Kind.CAP)
        self.why = ("not_cold", {"outdoor": outdoor, "limit": limit})
        return None
