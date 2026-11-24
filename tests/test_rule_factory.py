"""The rule chain factory (#96): every rule in priority order, wired to the shutter's schedule settings."""

from zoneinfo import ZoneInfo

from core.daily import SleepIn
from core.heat import SunSettings
from core.manual import ManualPause
from core.model import Inputs, ShutterConfig, ShutterContext
from core.rule_factory import build_rules
from core.schedule import DaySchedule, HolidayCalendar, SunTimes, merged

TZ = ZoneInfo("Europe/Amsterdam")


def rules(values=None, wanted=lambda ctx: 40, close_above=None):
    schedule_values = merged(None, values)
    schedule = DaySchedule(schedule_values, SunTimes(52.0, 5.0), HolidayCalendar(), TZ)
    return build_rules(
        schedule,
        schedule_values,
        SunSettings(),
        SleepIn(),
        ManualPause(),
        lambda: 20,
        wanted,
        close_above=close_above,
    )


def ctx(storm=False, outdoor=None):
    return ShutterContext(ShutterConfig("cover.a", 180), Inputs(now=0, storm=storm, outdoor=outdoor), 50, 100)


def test_every_rule_in_priority_order():
    built = rules()
    names = [rule.name for rule in built.chain.rules]
    assert names[0] == "storm" and names[-1] == "schedule"
    priorities = [rule.priority for rule in built.chain.rules]
    assert priorities == sorted(priorities)
    for rule in (built.storm, built.pause, built.heat, built.glare, built.schedule):
        assert rule in built.chain.rules


def test_storm_uses_the_schedule_setting_and_the_wanted_position():
    built = rules({"storm_position": "nearest"}, wanted=lambda ctx: 80)
    decision = built.chain.decide(ctx(storm=True))
    assert decision.reason == "storm" and decision.position == 100  # 80 is nearer to open than to closed


def test_temperature_limits_come_from_the_safety_settings():
    decision = rules(close_above=30).chain.decide(ctx(outdoor=31))
    assert decision.reason == "heat_limit" and decision.position == 0
