"""Rules and the chain that asks them in order of priority (chain of responsibility)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol, cast

from .model import Decision, Kind, Reason, ShutterContext


class Rule(Protocol):
    """One reason to move a shutter. Lower priority numbers are asked first."""

    priority: int

    def propose(self, ctx: ShutterContext) -> Decision | None: ...


Why = tuple[str, dict[str, Any]]  # a code and its values, set by a rule during propose (#56)


@dataclass(frozen=True)
class TraceEntry:
    """What one rule said in a decision (#56)."""

    rule: str
    priority: int
    result: str  # target | cap | final | none
    position: int | None = None
    applied: bool = False
    why: str | None = None
    values: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"rule": self.rule, "priority": self.priority, "result": self.result}
        if self.result != "none":
            data["position"] = self.position
            data["applied"] = self.applied
        if self.why:
            data["why"] = self.why
            if self.values:
                data["values"] = self.values
        return data


def rule_name(rule: object) -> str:
    return getattr(rule, "name", None) or type(rule).__name__


def _entry(rule: Rule, decision: Decision | None) -> TraceEntry:
    why: Why | None = getattr(rule, "why", None)
    code, values = why if why else (None, {})
    if decision is None:
        result, position = "none", None
    else:
        result = "final" if decision.final else str(decision.kind)
        position = decision.position
    return TraceEntry(rule_name(rule), rule.priority, result, position, False, code, dict(values))


class RuleChain:
    """Asks every rule by priority: the first target wins, and every cap may lower it.

    Without a target, a cap lowers the current position when that is higher; it never raises a shutter.
    """

    def __init__(self, rules: Iterable[Rule] = ()) -> None:
        self.rules = sorted(rules, key=lambda r: r.priority)
        self.last_trace: list[TraceEntry] = []  # what every rule said in the last full decision (#56)

    def decide(self, ctx: ShutterContext, skip: object | None = None) -> Decision:
        """The decision of all rules; `skip` leaves one rule out (what would happen without it)."""
        target: Decision | None = None
        caps: list[Decision] = []
        trace: list[TraceEntry] = []
        source: dict[int, int] = {}  # id of a decision -> its index in the trace
        for rule in self.rules:
            if rule is skip:
                continue
            if hasattr(rule, "why"):
                rule.why = None
            decision = rule.propose(ctx)
            trace.append(_entry(rule, decision))
            if decision is None:
                continue
            source[id(decision)] = len(trace) - 1
            if decision.kind is Kind.CAP:
                caps.append(decision)
            elif target is None:
                target = decision
        result, applied = self._resolve(ctx, target, caps)
        if skip is None:
            self.last_trace = [
                TraceEntry(**{**e.__dict__, "applied": applied is not None and i == source.get(id(applied))})
                for i, e in enumerate(trace)
            ]
        return result

    @staticmethod
    def _resolve(
        ctx: ShutterContext, target: Decision | None, caps: list[Decision]
    ) -> tuple[Decision, Decision | None]:
        """The decision, and the rule's decision that set it."""
        if target is not None and target.final:
            return target, target
        cap = min(caps, key=lambda d: cast(int, d.position)) if caps else None  # a cap always has one
        base = target.position if target is not None else ctx.position
        if cap is not None and (base is None or cast(int, cap.position) < base):
            if (
                target is not None
                and target.module is not None
                and target.position is not None
                and target.position <= cast(int, cap.position)
            ):
                return target, target  # the slit (real 0 %) is below every cap
            return Decision(cap.position, cap.reason), cap
        if target is not None:
            return target, target
        return Decision(None, Reason.IDLE), None
