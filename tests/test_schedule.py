"""Schedules: inheritance, sun times, phases, holidays, sleep-in, manual detection and the pause."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from core.daily import ScheduleRule, SleepIn, SleepInRule
from core.manual import ManualDetector, ManualPause, ManualPauseRule, matches
from core.model import Decision, Inputs, Kind, Reason, ShutterConfig, ShutterContext
from core.rules import RuleChain
from core.schedule import (
    DaySchedule,
    HolidayCalendar,
    HolidayEntry,
    Phase,
    SunTimes,
    merged,
    overridden,
    parse_holidays,
    weekend_set,
)

TZ = ZoneInfo("Europe/Amsterdam")
SUN = SunTimes(52.0, 5.0)


def local(y, m, d, hh, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=TZ)


def test_inheritance():
    base = {"weekday_open": "08:30", "dusk_position": 40}
    assert merged(base, None)["weekday_open"] == "08:30"
    v = merged(
        base, {"weekday_open": "07:45", "dusk_position": None, "slit_phase": "none", "weekend_open": ""}
    )
    assert v["weekday_open"] == "07:45"  # override wins
    assert v["dusk_position"] == 40  # None inherits
    assert v["weekend_open"] == "10:30"  # empty inherits (default)
    assert v["slit_phase"] == "none"  # a phase removed
    assert overridden({"weekday_open": "07:45", "x": None, "y": ""}) == ["weekday_open"]
    changed = merged({**base, "weekday_open": "09:00"}, {"dusk_position": 20})
    assert changed["weekday_open"] == "09:00" and changed["dusk_position"] == 20


def test_sun_times_amsterdam():
    rise, set_ = SUN.sunrise_sunset(date(2026, 6, 21), TZ)
    assert rise.strftime("%H:%M") in ("05:17", "05:18", "05:19", "05:20")
    assert set_.strftime("%H:%M") in ("22:03", "22:04", "22:05", "22:06")
    rise, set_ = SUN.sunrise_sunset(date(2026, 12, 21), TZ)
    assert rise.hour == 8 and set_.hour == 16


def schedule(values=None, calendar=None):
    return DaySchedule(merged(None, values), SUN, calendar or HolidayCalendar(), TZ)


def test_weekday_and_weekend_phases():
    s = schedule()
    wed = date(2026, 11, 18)
    phases = [(t.at.strftime("%H:%M"), t.phase) for t in s.transitions(wed)]
    assert phases[:2] == [("08:00", Phase.SLIT), ("08:30", Phase.DAY)]
    assert phases[2][1] is Phase.DUSK and phases[3][1] is Phase.NIGHT
    sunset = SUN.sunrise_sunset(wed, TZ)[1]
    assert s.transitions(wed)[3].at == sunset + timedelta(minutes=15)
    sat = [(t.at.strftime("%H:%M"), t.phase) for t in s.transitions(date(2026, 11, 21))]
    assert sat[:2] == [("10:00", Phase.SLIT), ("10:30", Phase.DAY)]
    assert s.phase_at(local(2026, 11, 18, 7, 59)) is Phase.NIGHT
    assert s.phase_at(local(2026, 11, 18, 8, 10)) is Phase.SLIT
    assert s.phase_at(local(2026, 11, 18, 12)) is Phase.DAY
    assert s.phase_at(local(2026, 11, 18, 23)) is Phase.NIGHT
    nxt = s.next_change(local(2026, 11, 18, 23))
    assert nxt.phase is Phase.SLIT and nxt.at == local(2026, 11, 19, 8)


def test_options_no_slit_no_dusk_close_limits_and_sunrise():
    s = schedule(
        {"slit_phase": "none", "dusk_phase": False, "close_earliest": "17:30", "close_latest": "21:00"}
    )
    t = s.transitions(date(2026, 12, 21))
    assert [x.phase for x in t] == [Phase.DAY, Phase.NIGHT]
    assert t[-1].at == local(2026, 12, 21, 17, 30)  # sunset + 15 is earlier: not before 17:30
    t = s.transitions(date(2026, 6, 21))
    assert t[-1].at == local(2026, 6, 21, 21, 0)  # not after 21:00
    winter = schedule({"not_before_sunrise": True, "weekday_slit": "07:00", "weekday_open": "07:30"})
    rise = SUN.sunrise_sunset(date(2026, 12, 21), TZ)[0]
    assert winter.transitions(date(2026, 12, 21))[0].at == rise  # later than 07:00


def test_daylight_saving_days():
    s = schedule()
    for d in (date(2026, 3, 29), date(2026, 10, 25)):
        t = s.transitions(d)
        assert t[0].at == local(d.year, d.month, d.day, 10) and t[0].at.utcoffset() == t[0].at.utcoffset()


def test_holidays():
    entries, bad = parse_holidays("2026-12-24 Christmas Eve\n12-31 New Year's Eve\n\nbad line\n2026-02-30")
    assert entries == [
        HolidayEntry(2026, 12, 24, "Christmas Eve"),
        HolidayEntry(None, 12, 31, "New Year's Eve"),
    ]
    assert bad == [4, 5]
    excluded, _ = parse_holidays("2026-12-26")
    cal = HolidayCalendar(
        weekend_days=weekend_set(["sat", "sun"]),
        extra=entries,
        excluded=excluded,
        from_calendar={date(2026, 12, 25): "Christmas", date(2026, 12, 26): "Boxing Day"},
    )
    assert cal.is_free(date(2026, 12, 24)) and cal.holiday(date(2026, 12, 24)) == "Christmas Eve"
    assert cal.is_free(date(2027, 12, 31))  # every year
    assert cal.is_free(date(2026, 12, 25))
    assert not cal.is_free(date(2026, 12, 23)) and cal.holiday(date(2026, 12, 26)) is None  # excluded
    assert cal.is_free(date(2026, 11, 21))  # a Saturday
    assert [d for d, _ in cal.listing(2026)] == [date(2026, 12, 24), date(2026, 12, 25), date(2026, 12, 31)]
    s = DaySchedule(merged(None, None), SUN, cal, TZ)
    assert s.transitions(date(2026, 12, 24))[0].at == local(2026, 12, 24, 10)  # weekend times


def ctx(epoch, position=0):
    return ShutterContext(ShutterConfig("cover.a", 180), Inputs(now=epoch), position, 100)


def test_schedule_rule_and_slit():
    s = schedule()
    rule = ScheduleRule(s, lambda: 18)
    assert rule.propose(ctx(local(2026, 11, 18, 8, 10).timestamp())) == Decision(0, "schedule", module=18)
    assert rule.propose(ctx(local(2026, 11, 18, 12).timestamp())) == Decision(100, "schedule")
    # heat protection cannot raise the slit and does not lower it
    cap = type("Cap", (), {"priority": 40, "propose": lambda self, c: Decision(30, "sun", Kind.CAP)})()
    chain = RuleChain([rule, cap])
    assert chain.decide(ctx(local(2026, 11, 18, 8, 10).timestamp())).module == 18
    assert chain.decide(ctx(local(2026, 11, 18, 12).timestamp(), 100)) == Decision(30, "sun")


def test_sleep_in():
    s = schedule()
    sleep = SleepIn()
    rule = SleepInRule(sleep, s)
    sleep.arm(True, local(2026, 11, 17, 22).timestamp())
    assert rule.propose(ctx(local(2026, 11, 17, 23).timestamp())) is None  # night anyway
    assert rule.propose(ctx(local(2026, 11, 18, 9).timestamp())) == Decision(0, Reason.SLEEP_IN)
    assert (
        rule.propose(ctx(local(2026, 11, 18, 12, 1).timestamp())) is None and not sleep.armed
    )  # ended at 12
    later = SleepIn()
    later.arm(True, local(2026, 11, 18, 14).timestamp())  # switched on in the afternoon: for tomorrow
    rule = SleepInRule(later, s)
    assert rule.propose(ctx(local(2026, 11, 18, 15).timestamp())) is None and later.armed
    assert rule.propose(ctx(local(2026, 11, 19, 9).timestamp())) == Decision(0, Reason.SLEEP_IN)


def test_manual_detector():
    d = ManualDetector(travel_time=60)
    assert not d.observe(100, False, 0)  # first report
    d.sent(50, 100, 10)
    assert not d.observe(None, True, 11)  # own motor start
    assert not d.observe(75, True, 20)  # on the way
    assert not d.observe(None, False, 40)
    assert not d.observe(50, None, 55)  # late report of the target
    assert not d.observe(50, None, 60)
    assert d.observe(70, None, 200)  # long after: someone moved it
    d.sent(20, 70, 300)
    assert d.observe(90, None, 310)  # the other way
    assert d.observe(None, True, 400)  # motor without a command
    d2 = ManualDetector(travel_time=60)
    d2.observe(0, None, 0)
    d2.sent(100, 0, 1)
    assert not d2.observe(100, None, 50)
    assert d2.at_rest(200)


def test_manual_pause_modes_and_rule():
    p = ManualPause()
    assert p.start(0, "until_next_phase", 120, "day", "switch")
    rule = ManualPauseRule(p, lambda now: "day" if now < 1000 else "dusk")
    assert rule.propose(ctx(500)) == Decision(None, Reason.MANUAL, final=True)
    assert rule.propose(ctx(1500)) is None and not p.on  # next phase
    p.start(0, "for_duration", 10, "day", "entity")
    assert p.still(599, "dusk") and not p.still(600, "dusk")
    assert not p.start(0, "ignore", 10, "day", "switch") and not p.on
    p.start(5, "for_duration", 10, "day", "switch")
    assert ManualPause.from_dict(p.to_dict()) == p
    assert matches(99, 100) and matches(102, 100) and not matches(96, 100) and not matches(50, None)
    safety = type("S", (), {"priority": 10, "propose": lambda self, c: Decision(100, "storm", final=True)})()
    p.start(0, "until_next_phase", 0, "day", "switch")
    assert RuleChain([rule, safety]).decide(ctx(1)) == Decision(100, "storm", final=True)


def test_disabled_calendar_holidays_count_as_normal_days_every_year():
    cal = HolidayCalendar(
        from_calendar={
            date(2026, 4, 6): "Easter Monday",
            date(2027, 3, 29): "Easter Monday",
            date(2026, 12, 25): "Christmas",
        },
        disabled=frozenset({"Easter Monday"}),
    )
    assert cal.holiday(date(2026, 4, 6)) is None and cal.holiday(date(2027, 3, 29)) is None
    assert cal.holiday(date(2026, 12, 25)) == "Christmas"
    assert cal.calendar_names() == [("Easter Monday", date(2026, 4, 6)), ("Christmas", date(2026, 12, 25))]
