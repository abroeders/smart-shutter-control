"""Locks set by an automation (#52): the modes, their order among the rules, expiry and the stored form."""

import pytest
from core.lock import Lock, LockMode, LockRule
from core.model import Decision, Inputs, Kind, Reason, ShutterConfig, ShutterContext
from core.rules import RuleChain
from core.weather import FrostRule, StormRule


class Fixed:
    """A rule that always proposes the same decision, like the schedule (target) or heat (cap)."""

    def __init__(self, priority: int, decision: Decision) -> None:
        self.priority = priority
        self.decision = decision

    def propose(self, ctx):
        return self.decision


def ctx(now: float = 0, position: int | None = 50, max_position: int = 100, **inputs) -> ShutterContext:
    return ShutterContext(ShutterConfig("cover.a", 180), Inputs(now=now, **inputs), position, max_position)


def locked(mode: LockMode | str, now: float = 0, duration: float | None = None) -> Lock:
    lock = Lock()
    lock.set(mode, now, duration)
    return lock


@pytest.mark.parametrize(
    ("mode", "position"),
    [("hold", None), ("force_open", 100), ("force_closed", 0)],
)
def test_each_mode_decides_finally(mode, position):
    rule = LockRule(locked(mode))
    assert rule.propose(ctx()) == Decision(position, Reason.LOCKED, final=True)
    assert rule.why == ("locked", {"mode": mode})


def test_no_lock_proposes_nothing():
    rule = LockRule(Lock())
    assert rule.propose(ctx()) is None
    assert rule.why == ("unlocked", {})
    assert LockRule(locked("none")).propose(ctx()) is None


def test_force_open_is_not_lowered_by_the_maximum_position():
    decision = LockRule(locked("force_open")).propose(ctx(max_position=60))
    assert decision is not None and decision.position == 100  # the controller then skips the maximum


def _chain(lock: Lock) -> RuleChain:
    return RuleChain(
        [
            StormRule(lambda: "closed"),
            FrostRule(),
            LockRule(lock),
            Fixed(40, Decision(30, Reason.SUN, Kind.CAP)),  # heat
            Fixed(41, Decision(40, Reason.GLARE, Kind.CAP)),
            Fixed(60, Decision(70, Reason.SCHEDULE)),
        ]
    )


@pytest.mark.parametrize(("mode", "position"), [("hold", None), ("force_open", 100), ("force_closed", 0)])
def test_the_lock_wins_over_heat_glare_and_the_schedule(mode, position):
    decision = _chain(locked(mode)).decide(ctx())
    assert (decision.position, decision.reason) == (position, Reason.LOCKED)


def test_without_a_lock_the_lower_rules_decide():
    decision = _chain(Lock()).decide(ctx(position=100))
    assert (decision.position, decision.reason) == (30, Reason.SUN)


def test_storm_wins_over_the_lock():
    decision = _chain(locked("force_open")).decide(ctx(storm=True))
    assert (decision.position, decision.reason) == (0, Reason.STORM)


def test_frost_wins_over_the_lock():
    decision = _chain(locked("force_open")).decide(ctx(frost=True))
    assert (decision.position, decision.reason) == (None, Reason.FROST)


def test_a_lock_with_a_duration_expires():
    lock = locked("force_closed", now=1000, duration=3600)
    assert lock.until == 4600
    rule = LockRule(lock)
    assert rule.propose(ctx(now=4599)) is not None
    assert rule.propose(ctx(now=4600)) is None and not lock.on and lock.until is None
    assert rule.why == ("unlocked", {})


def test_a_lock_without_a_duration_does_not_expire():
    lock = locked("hold", now=0)
    assert lock.until is None and lock.still(10**9)


def test_none_has_no_end_time_and_a_new_lock_replaces_the_old():
    lock = locked("force_closed", now=0, duration=60)
    lock.set("force_open", 10)
    assert (lock.mode, lock.until) == (LockMode.FORCE_OPEN, None)
    lock.set("none", 20, 60)
    assert not lock.on and lock.until is None


def test_end_clears_the_lock():
    lock = locked("hold", duration=60)
    lock.end()
    assert lock.to_dict() == {"mode": "none", "until": None}


def test_to_dict_and_from_dict_round_trip():
    lock = locked("force_closed", now=100, duration=7200)
    assert lock.to_dict() == {"mode": "force_closed", "until": 7300}
    copy = Lock.from_dict(lock.to_dict())
    assert (copy.mode, copy.until) == (LockMode.FORCE_CLOSED, 7300)


@pytest.mark.parametrize("data", [None, {}, {"mode": "sideways", "until": 5}])
def test_from_dict_without_or_with_bad_data_is_no_lock(data):
    assert not Lock.from_dict(data).on


def test_an_expired_stored_lock_is_dropped_when_asked():
    lock = Lock.from_dict({"mode": "hold", "until": 50})
    assert lock.on  # loading keeps it; the controller drops it at start with still()
    assert not lock.still(50) and lock.to_dict() == {"mode": "none", "until": None}


def test_a_zero_duration_ends_at_once():
    from core.lock import Lock, LockMode

    lock = Lock()
    lock.set(LockMode.FORCE_CLOSED, 100.0, 0.0)
    assert lock.until == 100.0 and not lock.still(100.0)
