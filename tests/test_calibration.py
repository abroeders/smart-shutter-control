"""Calibration: the roller model, the monotone fallback, both directions and the direction tracker."""

import math
import random

import pytest
from core.calibration import (
    DirectionTracker,
    IdentityCalibration,
    MonotoneCurve,
    QuadraticCurve,
    RollerCalibration,
    fit_curve,
)
from core.model import Direction


def spiral(
    m: float, speed: float = 1.0, r0: float = 0.025, d: float = 0.012, height: float = 1.5, gap: float = 0.08
):
    """Real opening for a module position: a roller with radius r0 and slats of thickness d (metres)."""
    theta_total = 2 * math.pi * 14  # turns from closed to open
    theta = m * speed * theta_total
    wound = r0 * theta + d * theta**2 / (4 * math.pi)
    full = r0 * theta_total + d * theta_total**2 / (4 * math.pi)  # the module runs on to the limit switch
    return min(1.0, max(0.0, (wound - gap) / (full - gap)))


def test_quadratic_fits_the_roller_model():
    pts = [(m, spiral(m)) for m in (0.25, 0.5, 0.75)]
    c = QuadraticCurve.fit(pts)
    assert c is not None and c.b > 0 and c.residual < 0.01
    assert c.opening(0.5) < 0.5  # lower than half way at half the travel time
    for o in (0.1, 0.5, 0.9):
        assert c.opening(c.module(o)) == pytest.approx(o, abs=1e-6)
    assert c.module(0) == 0 and c.module(1) == 1
    assert 0 < c.lift < 0.25  # the gap zone near closed


def test_quadratic_with_noise_and_gap_points():
    rng = random.Random(1)
    pts = [(m, spiral(m) + rng.uniform(-0.01, 0.01)) for m in (0.2, 0.4, 0.6, 0.8)] + [(0.03, 0.0)]
    c = fit_curve(pts)
    assert isinstance(c, QuadraticCurve)
    assert c.opening(0.03) == 0.0  # the clipped gap zone


def test_monotone_fallback_for_odd_points():
    pts = [(0.25, 0.05), (0.5, 0.6), (0.75, 0.65)]  # not what a roller does
    c = fit_curve(pts)
    assert isinstance(c, MonotoneCurve)
    assert c.opening(0.5) == pytest.approx(0.6, abs=1e-6)
    ms = [i / 50 for i in range(51)]
    assert all(c.opening(a) <= c.opening(b) + 1e-9 for a, b in zip(ms, ms[1:], strict=False))
    assert c.opening(c.module(0.62)) == pytest.approx(0.62, abs=1e-3)


def test_both_directions_reach_the_same_real_position():
    up = [(m, spiral(m, speed=0.92)) for m in (0.25, 0.5, 0.75)]  # slower going up, one travel time
    down = [(m, spiral(m, speed=1.0)) for m in (0.75, 0.5, 0.25)]
    cal = RollerCalibration.from_data({"points": {"up": up, "down": down}})
    m_up, m_down = cal.to_module(50, Direction.UP), cal.to_module(50, Direction.DOWN)
    assert m_up != m_down
    assert abs(cal.from_module(m_up, Direction.UP) - 50) <= 1  # whole percents
    assert abs(cal.from_module(m_down, Direction.DOWN) - 50) <= 1
    assert spiral(m_up / 100, speed=0.92) == pytest.approx(spiral(m_down / 100), abs=0.015)  # same real place
    assert cal.to_module(0, Direction.DOWN) == 0 and cal.to_module(100, Direction.UP) == 100
    assert cal.summary()["up"]["model"] == "quadratic"


def test_one_direction_is_used_for_the_other_and_slit():
    cal = RollerCalibration.from_data(
        {"points": {"up": [(m, spiral(m)) for m in (0.25, 0.5, 0.75)]}, "slit": {"up": 0.1}}
    )
    assert cal.to_module(50, Direction.DOWN) == cal.to_module(50, Direction.UP)
    assert cal.slit(Direction.UP) == 10
    assert cal.slit(Direction.DOWN) == round(100 * cal.curve(Direction.DOWN).lift)


def test_no_data_is_identity():
    assert isinstance(RollerCalibration.from_data(None), IdentityCalibration)
    assert isinstance(RollerCalibration.from_data({"points": {"up": [(0.5, 0.4)]}}), IdentityCalibration)


def test_direction_tracker():
    t = DirectionTracker()
    assert t.current(20) is Direction.DOWN and t.current(80) is Direction.UP  # unknown after a restart
    t.observe(100)
    t.observe(60)
    assert t.direction is Direction.DOWN
    t.observe(60)  # standing still keeps it
    assert t.direction is Direction.DOWN
    t.expect(Direction.UP)
    assert t.current(60) is Direction.UP
