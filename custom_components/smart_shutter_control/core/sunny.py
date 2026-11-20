"""Is it sunny? PV power against a clear-sky reference that is learned per position of the sun."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

from .sun import SunPosition

AZ_CELL = 10.0  # degrees
EL_CELL = 5.0
KEEP_DAYS = 30
MIN_DAYS = 7  # days with data before a cell is trusted
PERCENTILE = 0.95
HYSTERESIS = 0.15


def _cell(sun: SunPosition) -> str:
    return f"{int(sun.azimuth // AZ_CELL)}:{int(sun.elevation // EL_CELL)}"


def _percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


class ClearSkyReference:
    """Per cell of the sky the highest PV power of each of the last 30 days (repository: to/from dict)."""

    def __init__(self, cells: dict[str, dict[str, float]] | None = None) -> None:
        self.cells: dict[str, dict[str, float]] = cells or {}

    def observe(self, sun: SunPosition, pv_power: float, now: float) -> None:
        if sun.elevation <= 0 or pv_power is None or pv_power < 0:
            return
        day = str(int(now // 86400))
        days = self.cells.setdefault(_cell(sun), {})
        days[day] = max(days.get(day, 0.0), pv_power)
        oldest = int(now // 86400) - KEEP_DAYS
        for d in [d for d in days if int(d) < oldest]:
            del days[d]

    def reference(self, sun: SunPosition) -> float | None:
        days = self.cells.get(_cell(sun), {})
        if len(days) < MIN_DAYS:
            return None
        return _percentile(list(days.values()), PERCENTILE)

    def to_dict(self) -> dict:
        return self.cells

    @classmethod
    def from_dict(cls, data: dict | None) -> ClearSkyReference:
        return cls({k: dict(v) for k, v in (data or {}).items()})


SUNNY_WEATHER = ("sunny", "partlycloudy")


@dataclass
class SunnyDetector:
    """Sun factor and sunny state with hysteresis; falls back while the reference is still young."""

    reference: ClearSkyReference = field(default_factory=ClearSkyReference)
    threshold: float = 0.6
    pv_peak_kw: float | None = None
    sunny: bool = False
    factor: float | None = None
    source: str = "geometry"

    def update(
        self, sun: SunPosition, pv_power: float | None, weather: str | None = None, now: float | None = None
    ) -> bool:
        now = time.time() if now is None else now
        if pv_power is not None:
            self.reference.observe(sun, pv_power, now)
        if sun.elevation <= 0:
            self.factor, self.source, self.sunny = 0.0, "night", False
            return self.sunny
        ref = self.reference.reference(sun) if pv_power is not None else None
        if ref is not None and ref > 0:
            self.source = "learned"
        elif pv_power is not None and self.pv_peak_kw:
            ref = 0.8 * self.pv_peak_kw * 1000 * math.sin(math.radians(sun.elevation))
            self.source = "pv_peak"
        else:
            ref = None
        if ref:
            self.factor = max(0.0, min(1.0, pv_power / ref))
            limit = self.threshold - HYSTERESIS if self.sunny else self.threshold
            self.sunny = self.factor >= limit
        elif weather is not None:
            self.factor, self.source = None, "weather"
            self.sunny = weather in SUNNY_WEATHER
        else:
            self.factor, self.source, self.sunny = None, "geometry", True
        return self.sunny
