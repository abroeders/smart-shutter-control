"""Is it sunny? PV power against a clear-sky reference that is learned per position of the sun."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import ClassVar

from .sun import SunPosition

AZ_CELL = 10.0  # degrees
EL_CELL = 5.0
KEEP_DAYS = 30
MIN_DAYS = 7  # days with data before a cell is trusted
PERCENTILE = 0.95
HYSTERESIS = 0.15
LOW_SUN = 10.0  # degrees: below this the young PV curve is unreliable (diffuse light), #107


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

    def days(self, sun: SunPosition) -> int:
        """Days with data in the sky cell of this position of the sun (learned from `MIN_DAYS`)."""
        return len(self.cells.get(_cell(sun), {}))

    def to_dict(self) -> dict:
        return self.cells

    @classmethod
    def from_dict(cls, data: dict | None) -> ClearSkyReference:
        return cls({k: dict(v) for k, v in (data or {}).items()})


SUNNY_WEATHER = ("sunny", "partlycloudy")
LUX_LIMIT = 30000.0  # lux: sunny from this while the learned reference is young
LUX_HYSTERESIS = 0.2  # share of the limit


@dataclass
class PvBaseline:
    """PV power: while young, a rough clear-sky curve from the panels' peak power (if known). The curve
    only models direct light, so it never drops below its value at `LOW_SUN`, and below `LOW_SUN` the
    weather decides (#107)."""

    pv_peak_kw: float | None = None
    learned: ClassVar[str] = "learned"
    young: ClassVar[str] = "pv_peak"
    low_sun_source: ClassVar[str] = "pv_peak_weather"

    def young_reference(self, sun: SunPosition, threshold: float) -> float | None:
        if not self.pv_peak_kw:
            return None
        return 0.8 * self.pv_peak_kw * 1000 * math.sin(math.radians(max(sun.elevation, LOW_SUN)))

    def hysteresis(self, threshold: float, young: bool) -> float:
        return HYSTERESIS

    def low_sun(self, sun: SunPosition, weather: str | None) -> bool | None:
        """While young: sunny by the weather at a low sun; None leaves it to the factor."""
        if weather is None or sun.elevation >= LOW_SUN:
            return None
        return weather in SUNNY_WEATHER


@dataclass
class LuxBaseline:
    """Light sensors (lux): while young, a fixed limit. The factor is scaled so that the limit is the
    threshold, so the sun factor means the same before and after the reference is learned."""

    limit_lux: float = LUX_LIMIT
    learned: ClassVar[str] = "lux_learned"
    young: ClassVar[str] = "lux_limit"
    low_sun_source: ClassVar[str] = "lux_limit"

    def young_reference(self, sun: SunPosition, threshold: float) -> float | None:
        return self.limit_lux / threshold if threshold > 0 else None

    def hysteresis(self, threshold: float, young: bool) -> float:
        return threshold * LUX_HYSTERESIS if young else HYSTERESIS

    def low_sun(self, sun: SunPosition, weather: str | None) -> bool | None:
        return None  # a light sensor measures the light at the facade itself


@dataclass
class SunnyDetector:
    """Sun factor and sunny state with hysteresis, from PV power or lux; falls back while the reference
    is still young (strategy per source), then to the weather, then to geometry only."""

    reference: ClearSkyReference = field(default_factory=ClearSkyReference)
    threshold: float = 0.6
    pv_peak_kw: float | None = None
    baseline: PvBaseline | LuxBaseline | None = None
    sunny: bool = False
    factor: float | None = None
    source: str = "geometry"
    value: float | None = None

    def __post_init__(self) -> None:
        if self.baseline is None:
            self.baseline = PvBaseline(self.pv_peak_kw)

    def update(
        self, sun: SunPosition, value: float | None, weather: str | None = None, now: float | None = None
    ) -> bool:
        """`value`: PV power in W or illuminance in lux, depending on the baseline."""
        now = time.time() if now is None else now
        self.value = value
        if value is not None:
            self.reference.observe(sun, value, now)
        if sun.elevation <= 0:
            self.factor, self.source, self.sunny = 0.0, "night", False
            return self.sunny
        base = self.baseline
        assert base is not None  # set in __post_init__
        ref = self.reference.reference(sun) if value is not None else None
        young = False
        if ref is not None and ref > 0:
            self.source = base.learned
        elif value is not None and (ref := base.young_reference(sun, self.threshold)):
            self.source, young = base.young, True
        else:
            ref = None
        if ref and value is not None:
            self.factor = max(0.0, min(1.0, value / ref))
            limit = self.threshold - base.hysteresis(self.threshold, young) if self.sunny else self.threshold
            self.sunny = self.factor >= limit
            if young and (by_weather := base.low_sun(sun, weather)) is not None:
                self.source, self.sunny = base.low_sun_source, by_weather
        elif weather is not None:
            self.factor, self.source = None, "weather"
            self.sunny = weather in SUNNY_WEATHER
        else:
            self.factor, self.source, self.sunny = None, "geometry", True
        return self.sunny
