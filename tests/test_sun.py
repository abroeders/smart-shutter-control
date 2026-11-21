"""Sun position, window geometry, the clear-sky reference, caps in the rule chain and the heat rule."""

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from core.heat import HeatProtectionRule, Phase, SunSettings
from core.model import Decision, Inputs, Kind, ShutterConfig, ShutterContext
from core.rules import RuleChain
from core.sun import SunPosition, WindowGeometry
from core.sunny import ClearSkyReference, SunnyDetector


@pytest.mark.parametrize(
    ("lat", "lon", "when", "azimuth", "elevation"),
    [  # reference values from the astral library
        (52.0, 5.0, datetime(2026, 6, 21, 12, 0, tzinfo=UTC), 188.69, 61.23),
        (52.0, 5.0, datetime(2026, 12, 21, 8, 30, tzinfo=UTC), 137.72, 4.12),
        (52.0, 5.0, datetime(2026, 3, 20, 16, 0, tzinfo=UTC), 248.27, 16.16),
        (-33.9, 18.4, datetime(2026, 1, 15, 10, 0, tzinfo=UTC), 47.44, 72.22),
        (40.7, -74.0, datetime(2026, 9, 1, 20, 0, tzinfo=UTC), 244.34, 37.77),
    ],
)
def test_sun_position(lat, lon, when, azimuth, elevation):
    sun = SunPosition.at(lat, lon, when.timestamp())
    assert sun.azimuth == pytest.approx(azimuth, abs=0.3)
    assert sun.elevation == pytest.approx(elevation, abs=0.3)


def test_window_geometry():
    south, north, east = WindowGeometry(180), WindowGeometry(0), WindowGeometry(90)
    noon = SunPosition(180, 40)
    assert south.incidence(noon) == pytest.approx(40)
    assert south.sun_on(noon) and not north.sun_on(noon)
    morning = SunPosition(100, 15)
    assert east.sun_on(morning) and not south.sun_on(SunPosition(95, 10))  # sun nearly along the glass
    roof = WindowGeometry(180, tilt=30)
    assert roof.incidence(SunPosition(180, 60)) == pytest.approx(0, abs=1e-6)  # straight onto a 30° roof
    assert not WindowGeometry(180, min_elevation=20).sun_on(SunPosition(180, 15))  # behind a building
    assert not WindowGeometry(180, max_elevation=50).sun_on(SunPosition(180, 55))  # under an overhang
    assert not south.sun_on(SunPosition(180, -2))


def test_clear_sky_reference_learns_and_ignores_clouds():
    ref = ClearSkyReference()
    sun = SunPosition(180, 40)
    day = 86400
    for d in range(6):
        ref.observe(sun, 3000 if d % 2 else 800, d * day)
    assert ref.reference(sun) is None  # too young
    for d in range(6, 10):
        ref.observe(sun, 3000, d * day)
    assert ref.reference(sun) == pytest.approx(3000)  # the cloudy days do not pull it down
    copy = ClearSkyReference.from_dict(ref.to_dict())
    assert copy.reference(sun) == ref.reference(sun)
    ref.observe(sun, 2900, 60 * day)  # old days drop out
    assert ref.reference(sun) is None


def test_sunny_detector_fallbacks_and_hysteresis():
    sun = SunPosition(180, 30)
    d = SunnyDetector(pv_peak_kw=5.0)
    assert d.update(sun, 1800, now=0) and d.source == "pv_peak"  # 0.8·5000·sin 30° = 2000 → 0.9
    assert d.update(sun, 1000, now=60)  # 0.5: above 0.6 − 0.15
    assert not d.update(sun, 800, now=120)  # 0.4
    assert not d.update(sun, 1150, now=180)  # 0.575: below 0.6 again needed to start
    weather = SunnyDetector()
    assert weather.update(sun, None, "partlycloudy") and weather.source == "weather"
    assert not weather.update(sun, None, "cloudy")
    assert SunnyDetector().update(sun, None, None) and not SunnyDetector().update(SunPosition(180, -5), None)


@dataclass
class Fixed:
    priority: int
    decision: Decision

    def propose(self, ctx):
        return self.decision


def ctx(position=100, **inputs):
    return ShutterContext(ShutterConfig("cover.a", 180), Inputs(now=0, **inputs), position, 100)


def test_caps_lower_but_never_raise():
    cap = Fixed(40, Decision(30, "sun", Kind.CAP))
    assert RuleChain([cap, Fixed(60, Decision(100, "schedule"))]).decide(ctx()) == Decision(30, "sun")
    assert RuleChain([cap, Fixed(60, Decision(20, "schedule"))]).decide(ctx()) == Decision(20, "schedule")
    assert RuleChain([cap]).decide(ctx(position=100)) == Decision(30, "sun")  # lowers the current position
    assert RuleChain([cap]).decide(ctx(position=10)).position is None  # but does not raise it
    storm = Fixed(10, Decision(100, "storm", final=True))
    assert RuleChain([storm, cap]).decide(ctx()) == Decision(100, "storm", final=True)


NOON = SunPosition(180, 40)


def sun_ctx(now, sunny=True, outdoor=25.0, sun=NOON, heat=True, forecast_max=None):
    return ShutterContext(
        ShutterConfig("cover.a", 180),
        Inputs(now=now, outdoor=outdoor, sun=sun, sunny=sunny, forecast_max=forecast_max),
        100,
        100,
        heat_protection=heat,
        shading_position=30,
    )


def test_heat_rule_delays_and_passing_clouds():
    rule = HeatProtectionRule(SunSettings(close_delay=300, open_delay=1200))
    assert rule.propose(sun_ctx(-60, sunny=False)) is None  # running: the sun comes out later
    assert rule.propose(sun_ctx(0)) is None and rule.phase is Phase.PENDING
    assert rule.propose(sun_ctx(299)) is None
    assert rule.propose(sun_ctx(300)) == Decision(30, "sun", Kind.CAP)
    assert rule.propose(sun_ctx(400, sunny=False)) is not None  # a cloud: stays down for open_delay
    assert rule.propose(sun_ctx(800)) is not None and rule.phase is Phase.SHADING
    rule.propose(sun_ctx(900, sunny=False))
    assert rule.propose(sun_ctx(2099, sunny=False)) is not None
    assert rule.propose(sun_ctx(2100, sunny=False)) is None and rule.phase is Phase.OPEN


def test_heat_rule_opens_when_the_sun_leaves_the_window_and_needs_warmth():
    rule = HeatProtectionRule(SunSettings(close_delay=0))
    assert rule.propose(sun_ctx(0)) is not None
    assert rule.propose(sun_ctx(60, sun=SunPosition(280, 20))) is None  # behind the facade: open at once
    cool = HeatProtectionRule(SunSettings(close_delay=0))
    assert cool.propose(sun_ctx(0, outdoor=15.0)) is None
    off = HeatProtectionRule(SunSettings(close_delay=0))
    assert off.propose(sun_ctx(0, heat=False)) is None


def test_hot_day_lowers_at_a_low_outside_temperature():
    rule = HeatProtectionRule(SunSettings(close_delay=0, hot_day=28))
    assert rule.propose(sun_ctx(0, outdoor=15.0, forecast_max=30.0)) is not None


def test_forecast_below_the_hot_day_limit_does_not_replace_temperature():
    rule = HeatProtectionRule(SunSettings(close_delay=0, hot_day=28))
    assert rule.propose(sun_ctx(0, outdoor=15.0, forecast_max=27.9)) is None


def test_forecast_without_a_value_or_with_hot_day_off_changes_nothing():
    rule = HeatProtectionRule(SunSettings(close_delay=0, hot_day=28))
    assert rule.propose(sun_ctx(0, outdoor=15.0, forecast_max=None)) is None
    off = HeatProtectionRule(SunSettings(close_delay=0, hot_day=None))
    assert off.propose(sun_ctx(0, outdoor=15.0, forecast_max=30.0)) is None


def test_too_cold_trace_includes_forecast_and_limit():
    rule = HeatProtectionRule(SunSettings(close_delay=0, hot_day=28))
    rule.propose(sun_ctx(0, outdoor=15.0, forecast_max=24.0))
    assert rule.why == (
        "too_cold",
        {"outdoor": 15.0, "limit": 22.0, "forecast": 24.0, "forecast_limit": 28.0},
    )


def test_lux_start_limit_with_hysteresis_then_learned():
    from core.sunny import ClearSkyReference, LuxBaseline, SunnyDetector

    sun = SunPosition(180, 30)
    d = SunnyDetector(threshold=0.6, baseline=LuxBaseline(30000))
    assert not d.update(sun, 20000, None, 0) and d.source == "lux_limit"
    assert d.factor == pytest.approx(20000 / 50000)
    assert d.update(sun, 30000, None, 0) and d.factor == pytest.approx(0.6)
    assert d.update(sun, 25000, None, 0)  # above 80 % of the limit: still sunny
    assert not d.update(sun, 23000, None, 0)
    # a week of clear days at 80 000 lux: the learned reference takes over
    ref = ClearSkyReference()
    for day in range(8):
        ref.observe(sun, 80000, day * 86400)
    learned = SunnyDetector(reference=ref, threshold=0.6, baseline=LuxBaseline())
    assert learned.update(sun, 60000, None, 8 * 86400) and learned.source == "lux_learned"
    assert learned.factor == pytest.approx(0.75)
    assert not learned.update(sun, 30000, None, 8 * 86400)  # 30 000 lux is cloudy against 80 000


def test_lux_without_value_falls_back_to_the_weather():
    from core.sunny import LuxBaseline, SunnyDetector

    d = SunnyDetector(baseline=LuxBaseline())
    assert d.update(SunPosition(180, 30), None, "sunny", 0) and d.source == "weather"


def test_heat_rule_after_a_restart_acts_at_once():
    """The conditions held already before the restart: shading at once, not open for the close delay."""
    rule = HeatProtectionRule(SunSettings(close_delay=300))
    assert rule.propose(sun_ctx(0)) == Decision(30, "sun", Kind.CAP)
