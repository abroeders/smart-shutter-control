"""Converting between the real position of a shutter and the position its module works with (#10).

Module positions follow the travel time; real positions are the opening below the bottom bar as a share
of the window height. The roller grows while it winds, so per direction the real opening is a clipped
quadratic in the module position (see docs/design/2026-11-20-calibration.md). All fractions here are
0 (closed) … 1 (open).
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from .model import Direction

Point = tuple[float, float]  # (module position, real opening), fractions
MAX_RESIDUAL = 0.03  # above this the quadratic is not trusted


class Calibration(Protocol):
    calibrated: bool

    def to_module(self, position: int, direction: Direction) -> int:
        """Module position to send for a real position, reached moving in this direction."""

    def from_module(self, position: int, direction: Direction) -> int:
        """Real position for a module position, reached moving in this direction."""

    def slit(self, direction: Direction) -> int | None:
        """Module position with open slat gaps and the bottom bar still on the sill."""


class IdentityCalibration:
    """No calibration: the module position is the real position."""

    calibrated = False

    def to_module(self, position: int, direction: Direction) -> int:
        return position

    def from_module(self, position: int, direction: Direction) -> int:
        return position

    def slit(self, direction: Direction) -> int | None:
        return None


# --- curves (strategy) -----------------------------------------------------------------------------
class Curve(Protocol):
    residual: float

    def opening(self, m: float) -> float: ...

    def module(self, o: float) -> float: ...


def _clip(x: float) -> float:
    return min(1.0, max(0.0, x))


def _residual(curve: Curve, points: Sequence[Point]) -> float:
    return max((abs(curve.opening(m) - o) for m, o in points), default=0.0)


@dataclass(frozen=True)
class QuadraticCurve:
    """o(m) = clamp(a·m + b·m² − c, 0, 1) with b ≥ 0 (the roller only grows).

    The slower direction may not be fully open at the end of the module's travel time: the module runs on to
    its limit switch, so o(1) can be below 1 and the curve is clipped at 1 beyond it.
    """

    a: float
    b: float
    c: float
    residual: float = 0.0

    @property
    def lift(self) -> float:
        """Module position where the bottom bar leaves the sill."""
        return self._solve(0.0)

    def opening(self, m: float) -> float:
        return _clip(self.a * m + self.b * m * m - self.c)

    def _solve(self, o: float) -> float:
        rhs = self.c + o  # a·m + b·m² = rhs
        if self.b < 1e-12:
            return _clip(rhs / self.a)
        return _clip((-self.a + math.sqrt(self.a * self.a + 4 * self.b * rhs)) / (2 * self.b))

    def module(self, o: float) -> float:
        if o <= 0:
            return 0.0
        if o >= 1 or o >= self.opening(1.0):
            return 1.0  # the module's end position: it runs on to the limit switch
        return self._solve(o)

    def increasing(self) -> bool:
        return self.a + 2 * self.b * self.lift > 0 and self.a + 2 * self.b > 0

    @classmethod
    def fit(cls, points: Sequence[Point]) -> QuadraticCurve | None:
        """Least squares through the points above the sill; None if there is too little data.

        Three or more points: a, b and c free. Two points: with the end fixed at o(1) = 1.
        """
        lifted = [(m, o) for m, o in points if o > 0 and m < 1]
        if len(lifted) < 2:
            return None
        fitted = _free_fit(lifted) if len(lifted) >= 3 else None
        if fitted is None:
            fitted = _end_fixed_fit(lifted)
        if fitted is None:
            return None
        a, b, c = fitted
        if a <= 0 and b <= 0:
            return None
        curve = cls(a, b, c)
        return cls(a, b, c, _residual(curve, points))


def _solve3(m: list[list[float]], v: list[float]) -> list[float] | None:
    """Solve a 3 × 3 linear system (Cramer's rule)."""

    def det(a: list[list[float]]) -> float:
        return (
            a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
            - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
            + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])
        )

    d = det(m)
    if abs(d) < 1e-12:
        return None
    out = []
    for col in range(3):
        mc = [row[:] for row in m]
        for r in range(3):
            mc[r][col] = v[r]
        out.append(det(mc) / d)
    return out


def _free_fit(points: Sequence[Point]) -> tuple[float, float, float] | None:
    """o = a·m + b·m² − c, least squares; b < 0 (a shrinking roller) falls back to a straight line."""
    rows = [(m, m * m, -1.0) for m, _ in points]
    ata = [[sum(r[i] * r[j] for r in rows) for j in range(3)] for i in range(3)]
    atv = [sum(r[i] * o for r, (_, o) in zip(rows, points, strict=True)) for i in range(3)]
    sol = _solve3(ata, atv)
    if sol is None:
        return None
    a, b, c = sol
    if b >= 0:
        return a, b, c
    n = len(points)
    mean_m = sum(m for m, _ in points) / n
    mean_o = sum(o for _, o in points) / n
    sxx = sum((m - mean_m) ** 2 for m, _ in points)
    if sxx == 0:
        return None
    a = sum((m - mean_m) * (o - mean_o) for m, o in points) / sxx
    return a, 0.0, a * mean_m - mean_o


def _end_fixed_fit(points: Sequence[Point]) -> tuple[float, float, float] | None:
    """As _free_fit, with o(1) = 1: o − 1 = a·(m − 1) + b·(m² − 1)."""
    sxx = sxy = syy = sxz = syz = 0.0
    for m, o in points:
        x, y, z = m - 1, m * m - 1, o - 1
        sxx += x * x
        sxy += x * y
        syy += y * y
        sxz += x * z
        syz += y * z
    det = sxx * syy - sxy * sxy
    if abs(det) > 1e-12:
        a = (sxz * syy - syz * sxy) / det
        b = (syz * sxx - sxz * sxy) / det
        if b >= 0:
            return a, b, a + b - 1
    if not sxx:
        return None
    a = sxz / sxx
    return a, 0.0, a - 1


@dataclass(frozen=True)
class MonotoneCurve:
    """Monotone cubic (Fritsch–Carlson) through the points and the ends (0, 0) and (1, 1)."""

    xs: tuple[float, ...]
    ys: tuple[float, ...]
    slopes: tuple[float, ...]
    residual: float = 0.0

    def opening(self, m: float) -> float:
        xs, ys, d = self.xs, self.ys, self.slopes
        if m <= xs[0]:
            return ys[0]
        if m >= xs[-1]:
            return ys[-1]
        k = max(i for i in range(len(xs) - 1) if xs[i] <= m)
        h = xs[k + 1] - xs[k]
        t = (m - xs[k]) / h
        h00, h10 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t
        h01, h11 = -2 * t**3 + 3 * t**2, t**3 - t**2
        return _clip(h00 * ys[k] + h10 * h * d[k] + h01 * ys[k + 1] + h11 * h * d[k + 1])

    def module(self, o: float) -> float:
        if o <= 0:
            return 0.0
        if o >= 1:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(50):  # bisection: the curve is monotone
            mid = (lo + hi) / 2
            if self.opening(mid) < o:
                lo = mid
            else:
                hi = mid
        return hi

    @classmethod
    def fit(cls, points: Sequence[Point]) -> MonotoneCurve | None:
        merged: dict[float, float] = {0.0: 0.0, 1.0: 1.0}
        for m, o in points:
            merged[round(m, 4)] = o
        xs = sorted(merged)
        ys = [merged[x] for x in xs]
        for i in range(1, len(ys)):  # measurements that go down are measuring noise: keep the curve monotone
            ys[i] = max(ys[i], ys[i - 1])
        n = len(xs)
        if n < 3:
            return None
        delta = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
        d = [delta[0]] + [(delta[i - 1] + delta[i]) / 2 for i in range(1, n - 1)] + [delta[-1]]
        for i in range(n - 1):
            if delta[i] == 0:
                d[i] = d[i + 1] = 0.0
                continue
            alpha, beta = d[i] / delta[i], d[i + 1] / delta[i]
            s = alpha * alpha + beta * beta
            if s > 9:
                tau = 3 / math.sqrt(s)
                d[i], d[i + 1] = tau * alpha * delta[i], tau * beta * delta[i]
        curve = cls(tuple(xs), tuple(ys), tuple(d))
        return cls(curve.xs, curve.ys, curve.slopes, _residual(curve, points))


def fit_curve(points: Sequence[Point]) -> Curve | None:
    """The roller model when it fits within 3 % of the window height, else a monotone curve (factory).

    At least two measured points between the ends are needed.
    """
    if len([p for p in points if 0 < p[0] < 1]) < 2:
        return None
    quadratic = QuadraticCurve.fit(points)
    if quadratic is not None and quadratic.increasing() and quadratic.residual <= MAX_RESIDUAL:
        return quadratic
    return MonotoneCurve.fit(points) or quadratic


# --- the calibration --------------------------------------------------------------------------------
class RollerCalibration:
    """A curve per direction; a direction without enough points uses the other one."""

    calibrated = True

    def __init__(
        self, curves: Mapping[Direction, Curve], slits: Mapping[Direction, float] | None = None
    ) -> None:
        self.curves = dict(curves)
        self.slits = dict(slits or {})

    def curve(self, direction: Direction) -> Curve:
        if direction in self.curves:
            return self.curves[direction]
        return next(iter(self.curves.values()))

    def to_module(self, position: int, direction: Direction) -> int:
        """The whole module position whose real opening is closest to the requested one.

        Fully closed and fully open are always the module's own end positions (0 and 100), so it runs to
        its limit switches.
        """
        if position <= 0:
            return 0
        if position >= 100:
            return 100
        curve = self.curve(direction)
        exact = 100 * curve.module(position / 100)
        candidates = {max(0, min(100, int(exact))), max(0, min(100, int(exact) + 1))}
        return min(candidates, key=lambda m: (abs(100 * curve.opening(m / 100) - position), abs(m - exact)))

    def from_module(self, position: int, direction: Direction) -> int:
        if position <= 0:
            return 0
        if position >= 100:
            return 100  # at the limit switch, also for a direction whose curve ends just below 1
        return round(100 * self.curve(direction).opening(position / 100))

    def slit(self, direction: Direction) -> int | None:
        if direction in self.slits:
            return round(100 * self.slits[direction])
        curve = self.curve(direction)
        if isinstance(curve, QuadraticCurve):
            return round(100 * curve.lift)
        return None

    def summary(self) -> dict:
        out = {}
        for direction, curve in self.curves.items():
            out[str(direction)] = {
                "model": "quadratic" if isinstance(curve, QuadraticCurve) else "monotone",
                "residual": round(curve.residual * 100, 1),
                "module_at_50": round(100 * curve.module(0.5)),
            }
        return out

    @classmethod
    def from_data(cls, data: Mapping | None) -> Calibration:
        """From the stored calibration (subentry data); identity when there is nothing usable."""
        if not data:
            return IdentityCalibration()
        curves: dict[Direction, Curve] = {}
        for key, raw in (data.get("points") or {}).items():
            curve = fit_curve([(float(m), float(o)) for m, o in raw])
            if curve is not None:
                curves[Direction(key)] = curve
        if not curves:
            return IdentityCalibration()
        slits = {Direction(k): float(v) for k, v in (data.get("slit") or {}).items() if v is not None}
        return cls(curves, slits)


# --- direction of travel ----------------------------------------------------------------------------
class DirectionTracker:
    """The direction in which the shutter last moved; kept while it stands still."""

    def __init__(self) -> None:
        self.direction: Direction | None = None
        self._last: int | None = None

    def expect(self, direction: Direction) -> None:
        """A command was sent: its direction is known before the first report."""
        self.direction = direction

    def observe(self, module_position: int | None) -> None:
        if module_position is None:
            return
        if self._last is not None and module_position != self._last:
            self.direction = Direction.UP if module_position > self._last else Direction.DOWN
        self._last = module_position

    def current(self, module_position: int | None) -> Direction:
        if self.direction is not None:
            return self.direction
        return Direction.UP if (module_position or 0) >= 50 else Direction.DOWN


def points_from(raw: Iterable[Iterable[float]]) -> list[Point]:
    return [(float(m), float(o)) for m, o in raw]
