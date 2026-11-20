"""Rules and the chain that asks them in order of priority (chain of responsibility)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from .model import Decision, Kind, Reason, ShutterContext


class Rule(Protocol):
    """One reason to move a shutter. Lower priority numbers are asked first."""

    priority: int

    def propose(self, ctx: ShutterContext) -> Decision | None: ...


class RuleChain:
    """Asks every rule by priority: the first target wins, and every cap may lower it.

    Without a target, a cap lowers the current position when that is higher; it never raises a shutter.
    """

    def __init__(self, rules: Iterable[Rule] = ()) -> None:
        self.rules = sorted(rules, key=lambda r: r.priority)

    def decide(self, ctx: ShutterContext, skip: object | None = None) -> Decision:
        """The decision of all rules; `skip` leaves one rule out (what would happen without it)."""
        target: Decision | None = None
        caps: list[Decision] = []
        for rule in self.rules:
            if rule is skip:
                continue
            decision = rule.propose(ctx)
            if decision is None:
                continue
            if decision.kind is Kind.CAP:
                caps.append(decision)
            elif target is None:
                target = decision
        if target is not None and target.final:
            return target
        cap = min(caps, key=lambda d: d.position) if caps else None
        base = target.position if target is not None else ctx.position
        if cap is not None and (base is None or cap.position < base):
            slit = target is not None and target.module is not None and target.position is not None
            if slit and target.position <= cap.position:
                return target  # the slit (real 0 %) is below every cap
            return Decision(cap.position, cap.reason)
        return target or Decision(None, Reason.IDLE)
