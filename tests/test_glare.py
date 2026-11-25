"""Glare protection (#36): bright sun on the window lowers the shutter, whatever the temperature."""

from core.glare import GlareProtectionRule
from core.heat import HeatProtectionRule, Phase, SunSettings
from core.model import Decision, Inputs, Kind, Reason, ShutterConfig, ShutterContext
from core.rules import RuleChain
from core.schedule import Phase as DayPhase
from core.sun import SunPosition
from core.winter import WinterRule

LOW_SUN = SunPosition(170, 15)  # a November midday sun, in front of a south window


def glare_ctx(
    now, factor=0.9, sun=LOW_SUN, outdoor=6.0, azimuth=180, glare=True, sunny=True, winter=False, **kw
):
    return ShutterContext(
        ShutterConfig("cover.a", azimuth),
        Inputs(now=now, outdoor=outdoor, sun=sun, sunny=sunny, sun_factor=factor, winter=winter),
        100,
        100,
        glare_protection=glare,
        glare_position=40,
        glare_from=0.7,
        **kw,
    )


def rule(phase=DayPhase.DAY, close_delay=300.0, open_delay=1200.0):
    return GlareProtectionRule(SunSettings(close_delay=close_delay, open_delay=open_delay), lambda now: phase)


def test_bright_sun_in_the_cold_lowers_to_the_glare_position_after_the_delay():
    r = rule()
    assert r.propose(glare_ctx(-60, factor=0.3)) is None  # running: the sun breaks through later
    assert r.propose(glare_ctx(0)) is None and r.phase is Phase.PENDING
    assert r.propose(glare_ctx(299)) is None
    assert r.propose(glare_ctx(300)) == Decision(40, Reason.GLARE, Kind.CAP)
    heat = HeatProtectionRule(SunSettings(close_delay=0))
    assert heat.propose(glare_ctx(300, heat_protection=True)) is None  # 6 °C: no heat protection


def test_only_when_the_sun_is_on_this_window():
    assert rule(close_delay=0).propose(glare_ctx(0, azimuth=0)) is None  # north window, sun in the south
    assert rule(close_delay=0).propose(glare_ctx(0, sun=SunPosition(270, 10))) is None  # along the glass


def test_bright_from_the_limit_with_hysteresis():
    r = rule(close_delay=0, open_delay=1200)
    assert r.propose(glare_ctx(0, factor=0.65)) is None  # below 70 %
    assert r.propose(glare_ctx(10, factor=0.75)) is not None
    assert r.propose(glare_ctx(20, factor=0.6)) is not None and r.phase is Phase.SHADING  # within 15 points
    assert r.propose(glare_ctx(30, factor=0.5)) is not None and r.phase is Phase.LEAVING
    assert r.propose(glare_ctx(1229, factor=0.5)) is not None
    assert r.propose(glare_ctx(1230, factor=0.5)) is None and r.phase is Phase.OPEN


def test_without_a_sun_factor_sunny_decides():
    assert rule(close_delay=0).propose(glare_ctx(0, factor=None, sunny=True)) is not None
    assert rule(close_delay=0).propose(glare_ctx(0, factor=None, sunny=False)) is None


def test_only_in_the_day_phase_and_ends_at_dusk():
    for phase in (DayPhase.SLIT, DayPhase.NIGHT, DayPhase.DUSK):
        assert rule(phase, close_delay=0).propose(glare_ctx(0)) is None
    phase = [DayPhase.DAY]
    r = GlareProtectionRule(SunSettings(close_delay=0), lambda now: phase[0])
    assert r.propose(glare_ctx(0)) is not None
    phase[0] = DayPhase.DUSK
    assert r.propose(glare_ctx(60)) is None  # at once, not after the open delay


def test_switched_off_does_nothing():
    assert rule(close_delay=0).propose(glare_ctx(0, glare=False)) is None


def test_glare_wins_in_winter_but_winter_closed_stays_closed():
    glare = rule(close_delay=0)
    winter = WinterRule(lambda: True, lambda: -5.0, lambda now: DayPhase.DAY, lambda: 20)

    class Open:
        priority = 60

        def propose(self, ctx):
            return Decision(100, Reason.SCHEDULE)

    chain = RuleChain([glare, winter, Open()])
    assert chain.decide(glare_ctx(0, winter=True)).position == 40
    assert chain.decide(glare_ctx(60, winter=True, outdoor=-8.0)) == Decision(0, Reason.WINTER)


def test_heat_and_glare_together_the_lower_wins():
    heat = HeatProtectionRule(SunSettings(close_delay=0))
    chain = RuleChain([heat, rule(close_delay=0)])
    assert chain.decide(glare_ctx(0, outdoor=25.0, heat_protection=True, shading_position=30)).position == 30
    chain = RuleChain([HeatProtectionRule(SunSettings(close_delay=0)), rule(close_delay=0)])
    assert chain.decide(glare_ctx(0, outdoor=25.0, heat_protection=True, shading_position=60)).position == 40


def test_after_a_restart_it_acts_at_once():
    assert rule().propose(glare_ctx(0)) == Decision(40, Reason.GLARE, Kind.CAP)


def test_the_trace_tells_what_every_rule_said():
    glare = rule(close_delay=0)
    heat = HeatProtectionRule(SunSettings(close_delay=0))

    class Open:
        priority = 60
        name = "schedule"

        def propose(self, ctx):
            return Decision(100, Reason.SCHEDULE)

    chain = RuleChain([heat, glare, Open()])
    assert chain.decide(glare_ctx(0, heat_protection=True)).position == 40
    trace = [e.as_dict() for e in chain.last_trace]
    assert trace[0] == {
        "rule": "heat",
        "priority": 40,
        "result": "none",
        "why": "too_cold",
        "values": {"outdoor": 6.0, "limit": 22.0},
    }
    assert trace[1] == {
        "rule": "glare",
        "priority": 41,
        "result": "cap",
        "position": 40,
        "applied": True,
        "why": "bright",
        "values": {"factor": 90, "limit": 55},
    }
    assert trace[2] == {
        "rule": "schedule",
        "priority": 60,
        "result": "target",
        "position": 100,
        "applied": False,
    }

    chain.decide(glare_ctx(60, factor=0.3))  # leaving: still capped, with the time left
    assert chain.last_trace[1].why == "leaving" and chain.last_trace[1].values["seconds"] == 1200


def test_the_trace_says_why_the_sun_is_not_on_the_window():
    r = rule(close_delay=0)
    r.propose(glare_ctx(0, sun=SunPosition(280, 4)))  # beyond the side of a south window
    assert r.why[0] == "not_facing" and r.why[1]["incidence"] > 85
    ctx = glare_ctx(0, sun=SunPosition(180, 4))
    object.__setattr__(ctx.config, "min_elevation", 5.0)
    r.propose(ctx)
    assert r.why == ("below_horizon", {"elevation": 4.0, "limit": 5.0})
    r.propose(glare_ctx(0, factor=0.5))
    assert r.why == ("not_bright", {"factor": 50, "limit": 70})


def test_a_final_target_is_the_applied_one():
    from core.weather import StormRule

    chain = RuleChain([StormRule(lambda: "open"), rule(close_delay=0)])
    ctx = glare_ctx(0)
    object.__setattr__(ctx.inputs, "storm", True)
    assert chain.decide(ctx).reason == Reason.STORM
    assert [e.applied for e in chain.last_trace] == [True, False]
    assert chain.last_trace[1].result == "cap"


def away_glare(now, **kw):
    ctx = glare_ctx(now, **kw)
    object.__setattr__(ctx.inputs, "away", True)
    return ctx


def test_no_glare_protection_while_away():
    r = rule(close_delay=0)
    assert r.propose(away_glare(0)) is None
    assert r.why == ("away", {})
    assert r.propose(glare_ctx(10)) is not None  # home again


def test_glare_that_was_active_ends_through_the_open_delay_when_away():
    r = rule(close_delay=0, open_delay=1200)
    assert r.propose(glare_ctx(0)) is not None
    assert r.propose(away_glare(10)) is not None and r.phase is Phase.LEAVING
    assert r.propose(away_glare(1209)) is not None
    assert r.propose(away_glare(1210)) is None and r.phase is Phase.OPEN
