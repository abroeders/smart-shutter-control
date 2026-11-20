"""Winter mode: the 24-hour mean, detection with hysteresis, and the winter rule."""

import pytest
from core.model import Decision, Inputs, Kind, Reason, ShutterConfig, ShutterContext
from core.rules import RuleChain
from core.schedule import Phase
from core.winter import OutdoorMean, WinterDetector, WinterRule

H = 3600.0


def test_time_weighted_mean():
    m = OutdoorMean()
    assert m.mean(0) is None
    m.add(10, 0)
    m.add(10, 3600)  # unchanged: not stored again
    m.add(4, 18 * H)
    assert m.mean(24 * H) == pytest.approx((10 * 18 + 4 * 6) / 24)
    m.add(0, 30 * H)
    # window 12 h..36 h: 10 °C for 6 h (held from 0 h), 4 °C for 12 h, 0 °C for 6 h
    assert m.mean(36 * H) == pytest.approx((10 * 6 + 4 * 12 + 0 * 6) / 24)
    copy = OutdoorMean.from_dict(m.to_dict())
    assert copy.mean(36 * H) == m.mean(36 * H)


def test_detector_modes_and_hysteresis():
    d = WinterDetector(limit=12)
    assert d.update(11.5) and d.update(12.5)  # stays winter until 13
    assert not d.update(13.0)
    assert not d.update(None)
    assert WinterDetector(mode="on").update(20) and not WinterDetector(mode="off").update(0)


def ctx(phase_position=100, outdoor=5.0, winter=True, now=0.0):
    return ShutterContext(
        ShutterConfig("cover.a", 180), Inputs(now=now, outdoor=outdoor, winter=winter), phase_position, 100
    )


def rule(phase=Phase.DAY, closed_below=-5.0, enabled=True):
    return WinterRule(lambda: enabled, lambda: closed_below, lambda now: phase, lambda: 35)


def test_cold_day_closed_and_dusk_never_raises():
    assert rule().propose(ctx(outdoor=-6)) == Decision(0, Reason.WINTER)
    assert rule().propose(ctx(outdoor=-4)) is None
    assert rule(closed_below=None).propose(ctx(outdoor=-20)) is None
    assert rule().propose(ctx(winter=False, outdoor=-10)) is None
    assert rule(enabled=False).propose(ctx(outdoor=-10)) is None
    dusk = rule(phase=Phase.DUSK)
    assert dusk.propose(ctx(phase_position=0)) == Decision(0, Reason.WINTER, Kind.CAP)  # stays closed
    assert dusk.propose(ctx(phase_position=100)) is None  # open: down to the dusk position as usual
    schedule = type("S", (), {"priority": 60, "propose": lambda self, c: Decision(35, "schedule")})()
    assert RuleChain([dusk, schedule]).decide(ctx(phase_position=0)).position == 0
    assert RuleChain([dusk, schedule]).decide(ctx(phase_position=100)).position == 35
