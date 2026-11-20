"""Value objects shared by the rules, the limiter and the controller."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .sun import SunPosition


class Reason(StrEnum):
    """Why a shutter is where it is. Rules add their own values (#3–#7)."""

    IDLE = "idle"  # no rule wants anything
    OFF = "off"  # automatic control switched off
    MANUAL = "manual"
    CALIBRATING = "calibrating"  # the calibration assistant is moving the shutter
    SUN = "sun"  # heat protection (#3)
    SCHEDULE = "schedule"  # the phase of the day (#4)
    SLEEP_IN = "sleep_in"  # sleeping in (#4)
    STORM = "storm"  # (#6)
    FROST = "frost"
    HEAT_LIMIT = "heat_limit"
    COLD_LIMIT = "cold_limit"


class Kind(StrEnum):
    TARGET = "target"  # the position a rule wants; the first target by priority wins
    CAP = "cap"  # the shutter may not be higher than this; all caps apply


class Direction(StrEnum):
    UP = "up"  # opening: towards 100 %
    DOWN = "down"  # closing: towards 0 %


@dataclass(frozen=True)
class ShutterConfig:
    """Settings of one shutter (a config subentry)."""

    cover: str
    azimuth: float  # window direction in degrees: 0 north, 90 east, 180 south, 270 west
    tilt: float = 90.0  # 90 = vertical window
    min_elevation: float = 0.0  # below: the sun is blocked
    max_elevation: float = 90.0  # above: the sun is blocked (overhang)
    room_temperature: str | None = None


@dataclass(frozen=True)
class Inputs:
    """Everything the rules may read, gathered once per tick for all shutters."""

    now: float  # epoch seconds
    outdoor: float | None = None
    pv_power: float | None = None
    wind: float | None = None
    gust: float | None = None
    sun: SunPosition | None = None
    sunny: bool = False
    sun_factor: float | None = None
    storm: bool = False
    frost: bool = False
    extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ShutterContext:
    """What a rule sees for one shutter."""

    config: ShutterConfig
    inputs: Inputs
    position: int | None  # current position, 0 closed … 100 open
    max_position: int
    room: float | None = None  # room temperature
    heat_protection: bool = True
    shading_position: int = 30


@dataclass(frozen=True)
class Decision:
    """What the controller wants: a position (or None: leave it), and why.

    `kind` says whether a rule wants this position (target) or allows at most this position (cap);
    a final target (safety) is not lowered by caps.
    """

    position: int | None
    reason: str
    kind: Kind = Kind.TARGET
    final: bool = False
    module: int | None = None  # a module position to send as is (the slit: gaps open, bar on the sill)
