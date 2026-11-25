"""The schedule rule and sleep-in (#4). No Home Assistant imports."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from .model import Decision, Reason, ShutterContext
from .schedule import DaySchedule, Phase


def moment(epoch: float) -> datetime:
    return datetime.fromtimestamp(epoch, UTC)


class ScheduleRule:
    """The target of the current phase of the day."""

    priority = 60
    name = "schedule"

    def __init__(self, schedule: DaySchedule, slit_module: Callable[[], int]) -> None:
        self.schedule = schedule
        self.slit_module = slit_module
        self.why: tuple[str, dict] | None = None  # (#56)

    def phase(self, now: float) -> Phase:
        return self.schedule.phase_at(moment(now))

    def propose(self, ctx: ShutterContext) -> Decision | None:
        phase = self.phase(ctx.inputs.now)
        self.why = ("phase", {"phase": str(phase)})
        if ctx.inputs.holiday:  # presence simulation (#51)
            today = moment(ctx.inputs.now).astimezone(self.schedule.tz).date()
            morning, evening = self.schedule.shifts(today)
            self.why[1].update(shift_morning=morning, shift_evening=evening)
        if phase is Phase.SLIT:
            return Decision(0, Reason.SCHEDULE, module=self.slit_module())
        return Decision(self.schedule.target(phase), Reason.SCHEDULE)


@dataclass
class SleepIn:
    armed: bool = False
    armed_at: float = 0.0
    on_change: Callable[[], None] | None = None

    def arm(self, on: bool, now: float) -> None:
        self.armed, self.armed_at = on, now if on else 0.0
        if self.on_change:
            self.on_change()


class SleepInRule:
    """Closed during the slit and day phases until the sleep-in end time; then it switches itself off."""

    priority = 30
    name = "sleep_in"

    def __init__(self, sleep_in: SleepIn, schedule: DaySchedule) -> None:
        self.sleep_in = sleep_in
        self.schedule = schedule
        self.why: tuple[str, dict] | None = None  # (#56)

    def propose(self, ctx: ShutterContext) -> Decision | None:
        if not self.sleep_in.armed:
            self.why = ("off", {})
            return None
        now = moment(ctx.inputs.now)
        if self.schedule.phase_at(now) not in (Phase.SLIT, Phase.DAY):
            return None
        until = self.schedule.sleep_in_until(now)
        if until.timestamp() <= self.sleep_in.armed_at:
            return None  # switched on after today's end: it is for tomorrow morning
        if now >= until:
            self.sleep_in.arm(False, ctx.inputs.now)
            return None
        return Decision(0, Reason.SLEEP_IN)
