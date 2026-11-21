"""Storm and frost detection, and the safety rules."""

from core.model import Decision, Inputs, Reason, ShutterConfig, ShutterContext
from core.rules import RuleChain
from core.weather import (
    FrostDetector,
    FrostRule,
    StormDetector,
    StormRule,
    TemperatureLimitRule,
    cloud_coverage,
    storm_target,
)


def test_storm_each_source_its_own_limit_and_release():
    s = StormDetector(wind_limit=50, gust_limit=70, release=900)
    assert not s.update(40, 65, 0)
    assert s.update(40, 72, 10) and s.source == "gust" and s.value == 72 and s.since == 10
    assert s.update(20, 30, 800) and s.until == 910  # still within the release time
    assert not s.update(20, 30, 910)
    assert s.update(55, None, 1000) and s.source == "wind"  # the gust source unavailable
    assert not StormDetector(wind_limit=None, gust_limit=None).update(200, 200, 0)


def test_frost_and_release():
    f = FrostDetector(limit=0, release=3600)
    assert not f.update(2, 0)
    assert f.update(-1, 10)
    assert f.update(1, 100) and f.update(None, 200)
    assert not f.update(1, 100 + 3600)


def test_storm_target():
    assert storm_target(60, "nearest", 100) == 100 and storm_target(40, "nearest", 100) == 0
    assert storm_target(10, "open", 100) == 100 and storm_target(90, "closed", 100) == 0
    assert storm_target(90, "nearest", 80) == 0  # never above a maximum below 100 %
    # the end nearest to what the schedule wants: locked open by day, closed when the evening starts
    assert storm_target(100, "nearest", 100, wanted=0) == 0
    assert storm_target(0, "nearest", 100, wanted=100) == 100
    assert storm_target(100, "nearest", 100, wanted=35) == 0  # dusk


def ctx(position=60, **inputs):
    return ShutterContext(ShutterConfig("cover.a", 180), Inputs(now=0, **inputs), position, 100)


def test_storm_follows_the_evening():
    wanted = {"value": 100}
    rule = StormRule(lambda: "nearest", lambda c: wanted["value"])
    assert rule.propose(ctx(position=100, storm=True)).position == 100
    wanted["value"] = 0  # the night phase starts
    assert rule.propose(ctx(position=100, storm=True)).position == 0


def test_priorities():
    pause = type(
        "P", (), {"priority": 20, "propose": lambda self, c: Decision(None, Reason.MANUAL, final=True)}
    )()
    chain = RuleChain([pause, StormRule(lambda: "nearest"), FrostRule(), TemperatureLimitRule(30, -5)])
    assert chain.decide(ctx(storm=True)) == Decision(100, Reason.STORM, final=True)  # over a manual pause
    assert chain.decide(ctx(storm=True, frost=True)).reason == Reason.STORM  # storm also during frost
    assert chain.decide(ctx(frost=True)) == Decision(None, Reason.FROST, final=True)
    assert chain.decide(ctx(outdoor=31)) == Decision(0, Reason.HEAT_LIMIT, final=True)
    assert chain.decide(ctx(outdoor=29.5)).reason == Reason.HEAT_LIMIT  # hysteresis
    assert chain.decide(ctx(outdoor=28.9)).reason == Reason.MANUAL
    assert chain.decide(ctx(outdoor=-6)).reason == Reason.COLD_LIMIT
    assert RuleChain([TemperatureLimitRule(None, None)]).decide(ctx(outdoor=40)).position is None


def test_cloud_coverage_from_the_weather_attributes():
    assert cloud_coverage({"cloud_coverage": 55.5}) == 55.5
    assert cloud_coverage({"cloud_coverage": "120"}) == 100.0
    assert cloud_coverage({"cloud_coverage": None}) is None
    assert cloud_coverage({"temperature": 12}) is None
