"""Rules and the chain that asks them in order of priority (chain of responsibility)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from .model import Decision, Reason, ShutterContext


class Rule(Protocol):
    """One reason to move a shutter. Lower priority numbers are asked first."""

    priority: int

    def propose(self, ctx: ShutterContext) -> Decision | None: ...


class RuleChain:
    """Asks the rules by priority; the first one with a proposal decides."""

    def __init__(self, rules: Iterable[Rule] = ()) -> None:
        self.rules = sorted(rules, key=lambda r: r.priority)

    def decide(self, ctx: ShutterContext) -> Decision:
        for rule in self.rules:
            decision = rule.propose(ctx)
            if decision is not None:
                return decision
        return Decision(None, Reason.IDLE)
