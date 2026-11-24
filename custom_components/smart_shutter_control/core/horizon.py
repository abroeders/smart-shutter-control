"""The horizon of a window (#54): the lowest sun elevation per sun direction, from points the user records.

Buildings and trees block the low sun at different heights in different directions. Pure: no Home Assistant.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

REACH = 15.0  # degrees of azimuth the outermost points hold beyond themselves
NEAR = 3.0  # degrees of azimuth: a new point this close replaces the old one


@dataclass(frozen=True)
class Horizon:
    points: tuple[tuple[float, float], ...] = ()  # (azimuth, elevation), sorted by azimuth

    @classmethod
    def from_data(cls, data: Iterable[Sequence[float]] | None) -> Horizon:
        return cls(tuple(sorted((float(a), float(e)) for a, e in (data or []))))

    def as_data(self) -> list[list[float]]:
        return [[a, e] for a, e in self.points]

    def elevation_at(self, azimuth: float) -> float | None:
        """The horizon in this sun direction, or None where no point says anything."""
        points = self.points
        if not points:
            return None
        first, last = points[0], points[-1]
        if azimuth <= first[0]:
            return first[1] if first[0] - azimuth <= REACH else None
        if azimuth >= last[0]:
            return last[1] if azimuth - last[0] <= REACH else None
        for (a1, e1), (a2, e2) in zip(points, points[1:], strict=False):
            if a1 <= azimuth <= a2:
                return e1 if a2 == a1 else e1 + (e2 - e1) * (azimuth - a1) / (a2 - a1)
        return None

    def with_point(self, azimuth: float, elevation: float) -> Horizon:
        """The horizon with this point; a point within NEAR degrees of azimuth is replaced."""
        kept = [(a, e) for a, e in self.points if abs(a - azimuth) > NEAR]
        return Horizon(tuple(sorted([*kept, (round(azimuth, 1), round(elevation, 1))])))


# --- the table in the shutter's settings ----------------------------------------------------------------
def rows_from(horizon: Horizon) -> list[dict[str, float]]:
    return [{"azimuth": a, "elevation": e} for a, e in horizon.points]


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def check(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    """Error keys for the form; empty when the table can be used."""
    azimuths = [_number(r.get("azimuth")) for r in rows]
    elevations = [_number(r.get("elevation")) for r in rows]
    errors = []
    if any(a is None or not 0 <= a <= 360 for a in azimuths):
        errors.append("azimuth_range")
    elif len({round(cast(float, a), 1) for a in azimuths}) != len(azimuths):
        errors.append("azimuth_twice")
    if any(e is None or not 0 <= e <= 60 for e in elevations):
        errors.append("elevation_range")
    return errors


def from_rows(rows: Sequence[Mapping[str, Any]]) -> Horizon:
    return Horizon.from_data(
        [cast(float, _number(r["azimuth"])), cast(float, _number(r["elevation"]))] for r in rows
    )
