"""Calibration: the roller model, the monotone fallback, both directions and the position memory."""

import math
import random

import pytest
from core.calibration import (
    IdentityCalibration,
    MonotoneCurve,
    PositionMemory,
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


def test_whole_module_positions_give_the_closest_real_position():
    cal = RollerCalibration.from_data({"points": {"up": [[0.5, 0.25], [0.75, 0.58]]}})
    for target in range(0, 101, 5):
        assert cal.from_module(cal.to_module(target, Direction.UP), Direction.UP) == pytest.approx(
            target, abs=1
        )


def test_end_positions_are_the_module_ends():
    slow_up = [(m, spiral(m, speed=0.85)) for m in (0.25, 0.5, 0.75)]  # not fully open at the end of its time
    cal = RollerCalibration.from_data({"points": {"up": slow_up, "down": slow_up}})
    assert cal.curve(Direction.UP).opening(1.0) < 1.0
    for d in Direction:
        assert cal.to_module(0, d) == 0
        assert cal.to_module(100, d) == 100
        assert cal.from_module(0, d) == 0
        assert cal.from_module(100, d) == 100  # on the limit switch: fully open


def test_no_data_is_identity():
    assert isinstance(RollerCalibration.from_data(None), IdentityCalibration)
    assert isinstance(RollerCalibration.from_data({"points": {"up": [(0.5, 0.4)]}}), IdentityCalibration)


def position_calibration():
    return RollerCalibration.from_data(
        {
            "points": {
                "up": [[0.25, 0.05], [0.5, 0.5], [0.75, 0.95]],
                "down": [[0.25, 0.1], [0.5, 0.45], [0.75, 0.8]],
            }
        }
    )


def test_sent_real_position_is_used_until_module_leaves_tolerance():
    calibration = position_calibration()
    memory = PositionMemory()
    memory.command(50, 20, Direction.UP, 40)

    assert memory.real(49, calibration) == 20
    assert memory.real(51, calibration) == 20
    assert memory.real(52, calibration) == calibration.from_module(52, Direction.UP)
    assert memory.real(52, calibration) != 20


def test_reports_on_the_way_keep_sent_and_reports_away_clear_it():
    memory = PositionMemory()
    memory.command(60, 40, Direction.UP, 30)

    memory.observe(45)
    assert memory.sent is not None
    memory.observe(40)
    assert memory.sent is None


def test_small_reports_do_not_flip_direction_until_three_points():
    memory = PositionMemory(direction=Direction.UP, anchor=50)

    memory.observe(49)
    assert memory.direction is Direction.UP and memory.anchor == 50
    memory.observe(48)
    assert memory.direction is Direction.UP and memory.anchor == 50
    memory.observe(47)
    assert memory.direction is Direction.DOWN and memory.anchor == 47


def test_module_command_uses_the_curve():
    calibration = position_calibration()
    memory = PositionMemory()
    memory.command(50, None, Direction.DOWN, 70)

    assert memory.real(50, calibration) == calibration.from_module(50, Direction.DOWN)


def test_forget_sent_clears_the_remembered_command():
    memory = PositionMemory()
    memory.command(50, 20, Direction.UP, 40)

    memory.forget_sent()

    assert memory.sent is None


def test_position_memory_round_trip_and_bad_data():
    memory = PositionMemory()
    memory.command(65, 42, Direction.UP, 50)
    restored = PositionMemory.from_dict(memory.to_dict())
    assert restored.to_dict() == memory.to_dict()

    bad = PositionMemory.from_dict({"sent": [65, None, "sideways"], "direction": "up", "anchor": 50})
    assert bad.to_dict() == {"sent": None, "direction": None, "anchor": None}


def test_identity_calibration_ignores_sent_position():
    memory = PositionMemory()
    memory.command(50, 20, Direction.UP, 40)

    assert memory.real(50, IdentityCalibration()) == 50
