"""Core: imports without Home Assistant, the rule chain, the limiter and the identity calibration."""

import sys
from dataclasses import dataclass

from core.calibration import IdentityCalibration
from core.limits import PositionLimiter
from core.model import Decision, Direction, Inputs, Reason, ShutterConfig, ShutterContext
from core.rules import RuleChain


def test_core_imports_without_home_assistant():
    assert not any(name == "homeassistant" or name.startswith("homeassistant.") for name in sys.modules)


@dataclass
class FixedRule:
    priority: int
    position: int | None
    reason: str

    def propose(self, ctx):
        return None if self.position is None else Decision(self.position, self.reason)


def ctx(position=100, max_position=100):
    return ShutterContext(ShutterConfig("cover.a", 180), Inputs(now=0), position, max_position)


def test_chain_asks_by_priority_and_first_proposal_wins():
    chain = RuleChain(
        [FixedRule(50, 30, "schedule"), FixedRule(10, None, "storm"), FixedRule(20, 0, "manual")]
    )
    assert [r.priority for r in chain.rules] == [10, 20, 50]
    assert chain.decide(ctx()) == Decision(0, "manual")


def test_empty_chain_is_idle():
    assert RuleChain().decide(ctx()) == Decision(None, Reason.IDLE)


def test_limiter_maximum_position():
    lim = PositionLimiter()
    assert lim.limit(100, 80) == 80
    assert lim.limit(40, 80) == 40
    assert lim.limit(-5, 80) == 0
    assert lim.limit(120, 100) == 100


def test_limiter_storm_only_open_or_closed():
    lim = PositionLimiter()
    assert lim.limit(60, 100, storm=True) == 100
    assert lim.limit(40, 100, storm=True) == 0
    # a maximum position below 100: closed in a storm, never above the maximum
    assert lim.limit(80, 80, storm=True) == 0


def test_identity_calibration():
    cal = IdentityCalibration()
    for d in Direction:
        assert cal.to_module(37, d) == 37
        assert cal.from_module(37, d) == 37
