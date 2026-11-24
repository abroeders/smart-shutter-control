"""The calibration as a table (#40): a row per module position, the measured opening per direction.

Stored points are fractions 0 … 1 per direction; the table shows whole percentages. Pure: no Home Assistant.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

DIRECTIONS = ("up", "down")


def _percent(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return round(float(value))


def _module(row: Mapping[str, Any]) -> int:
    """The module position of a checked row."""
    return cast(int, _percent(row["module"]))


def rows_from(data: Mapping | None) -> list[dict[str, int]]:
    """Rows sorted by module position; a direction without a point at that position has no value."""
    rows: dict[int, dict[str, int]] = {}
    for direction in DIRECTIONS:
        for module, opening in ((data or {}).get("points") or {}).get(direction) or []:
            m = round(100 * float(module))
            rows.setdefault(m, {"module": m})[direction] = round(100 * float(opening))
    return [rows[m] for m in sorted(rows)]


def slits_from(data: Mapping | None) -> dict[str, int]:
    slit = (data or {}).get("slit") or {}
    return {d: round(100 * float(slit[d])) for d in DIRECTIONS if slit.get(d) is not None}


def check(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    """Error keys for the form; empty when the table can be used."""
    errors: list[str] = []
    modules = [_percent(r.get("module")) for r in rows]
    if any(m is None or not 1 <= m <= 99 for m in modules):
        errors.append("module_range")
    elif len(set(modules)) != len(modules):
        errors.append("module_twice")
    openings = [_percent(r.get(d)) for r in rows for d in DIRECTIONS]
    if any(o is not None and not 0 <= o <= 100 for o in openings):
        errors.append("opening_range")
    if errors:
        return errors
    counts = []
    for d in DIRECTIONS:
        points = sorted((_module(r), o) for r in rows if (o := _percent(r.get(d))) is not None)
        counts.append(len(points))
        if any(b[1] < a[1] for a, b in zip(points, points[1:], strict=False)):
            errors.append("opening_falls")
            break
    if max(counts, default=0) < 2:
        errors.append("too_few_points")
    return errors


def data_from(
    rows: Sequence[Mapping[str, Any]], slits: Mapping[str, Any], height_cm: float | None
) -> dict[str, Any]:
    """The stored calibration from checked rows and the optional slit positions."""
    points: dict[str, list[list[float]]] = {d: [] for d in DIRECTIONS}
    for row in sorted(rows, key=lambda r: _percent(r["module"]) or 0):
        for d in DIRECTIONS:
            opening = _percent(row.get(d))
            if opening is not None:
                points[d].append([_module(row) / 100, opening / 100])
    slit = {d: v / 100 for d in DIRECTIONS if (v := _percent(slits.get(d))) is not None}
    return {"window_height_cm": height_cm, "points": points, "slit": slit}
