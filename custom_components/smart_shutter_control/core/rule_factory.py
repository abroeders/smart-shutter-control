"""Factory for a shutter's rule chain (#96): every rule, built from the shutter's schedule and settings."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .daily import ScheduleRule, SleepIn, SleepInRule
from .glare import GlareProtectionRule
from .heat import HeatProtectionRule, SunSettings
from .lock import Lock, LockRule
from .manual import ManualPause, ManualPauseRule
from .model import ShutterContext
from .rules import RuleChain
from .schedule import DaySchedule
from .weather import FrostRule, StormRule, TemperatureLimitRule
from .winter import WinterRule


@dataclass(frozen=True)
class ShutterRules:
    """The chain and the rules the controller and its entities talk to directly."""

    chain: RuleChain
    schedule: ScheduleRule
    pause: ManualPauseRule
    lock: LockRule
    heat: HeatProtectionRule
    glare: GlareProtectionRule
    storm: StormRule


def build_rules(
    schedule: DaySchedule,
    values: Mapping[str, Any],
    sun: SunSettings,
    sleep_in: SleepIn,
    pause: ManualPause,
    slit_module: Callable[[], int],
    wanted_without_storm: Callable[[ShutterContext], int | None],
    close_above: float | None = None,
    close_below: float | None = None,
    lock: Lock | None = None,
) -> ShutterRules:
    """`values` are the shutter's schedule settings (the base schedule with its overrides), read when a rule
    decides; `wanted_without_storm` gives the position the other rules want, for the end of a storm."""
    schedule_rule = ScheduleRule(schedule, slit_module)
    pause_rule = ManualPauseRule(pause, lambda now: str(schedule_rule.phase(now)))
    heat = HeatProtectionRule(sun)
    glare = GlareProtectionRule(sun, schedule_rule.phase)
    storm = StormRule(lambda: str(values["storm_position"]), wanted_without_storm)
    lock_rule = LockRule(lock if lock is not None else Lock())
    chain = RuleChain(
        [
            storm,
            FrostRule(),
            lock_rule,
            TemperatureLimitRule(close_above, close_below),
            pause_rule,
            SleepInRule(sleep_in, schedule),
            heat,
            glare,
            WinterRule(
                lambda: _on(values["winter"]),
                lambda: _number(values["winter_closed_below"]),
                schedule_rule.phase,
                lambda: int(values["dusk_position"]),
            ),
            schedule_rule,
        ]
    )
    return ShutterRules(chain, schedule_rule, pause_rule, lock_rule, heat, glare, storm)


def _on(value: Any) -> bool:
    return value not in (False, "off", "none", "false", None)


def _number(value: Any) -> float | None:
    try:
        return None if value in (None, "", "none", "off") else float(value)
    except (TypeError, ValueError):
        return None
