"""Value objects shared by the rules, the limiter and the controller."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Reason(StrEnum):
    """Why a shutter is where it is. Rules add their own values (#3–#7)."""

    IDLE = "idle"  # no rule wants anything
    OFF = "off"  # automatic control switched off
    MANUAL = "manual"
    CALIBRATING = "calibrating"  # the calibration assistant is moving the shutter


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
    extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ShutterContext:
    """What a rule sees for one shutter."""

    config: ShutterConfig
    inputs: Inputs
    position: int | None  # current position, 0 closed … 100 open
    max_position: int


@dataclass(frozen=True)
class Decision:
    """What the controller wants: a position (or None: leave it), and why."""

    position: int | None
    reason: str
