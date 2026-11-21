"""The shading position from the sun (#55): low enough that direct sun reaches no further into the room than a
set depth, and no lower. Pure: no Home Assistant.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .sun import SunPosition

STEP = 10  # % : the position goes in steps, rounded down (more shade)
HOLD = 900.0  # s : at most one change per quarter of an hour


@dataclass(frozen=True)
class RoomGeometry:
    sill_cm: float  # the glass's lower edge above the floor
    window_cm: float  # the height of the glass
    depth_m: float  # direct sun may reach this far over the floor, from the window


def depth_position(room: RoomGeometry, sun: SunPosition, window_azimuth: float) -> int | None:
    """The highest real position (% of the window height) that keeps the sun within the depth, in steps.

    For a vertical window: the profile angle φ (tan φ = tan elevation / cos γ, γ the sun's angle to the window
    normal in the horizontal plane) lets light through the top of an opening o reach the floor at
    (sill + o) / tan φ. None when the sun is not in front of the window.
    """
    cos_g = math.cos(math.radians(sun.azimuth - window_azimuth))
    if sun.elevation <= 0 or cos_g <= 0.01 or room.window_cm <= 0:
        return None
    tan_phi = math.tan(math.radians(sun.elevation)) / cos_g
    opening = room.depth_m * 100 * tan_phi - room.sill_cm
    position = max(0.0, min(100.0, 100 * opening / room.window_cm))
    return int(position // STEP * STEP)


class DepthShading:
    """The position a protection rule uses: from the sun when the room geometry is known, else the fixed one.

    Never below the fixed position; changes at most once per HOLD while the protection lasts.
    """

    def __init__(self) -> None:
        self.position: int | None = None
        self.at = 0.0

    def reset(self) -> None:
        self.position = None

    def __call__(
        self,
        now: float,
        room: RoomGeometry | None,
        sun: SunPosition | None,
        window_azimuth: float,
        tilt: float,
        fixed: int,
    ) -> int:
        if room is None or sun is None or tilt != 90:
            return fixed
        if self.position is not None and now - self.at < HOLD:
            return max(fixed, self.position)
        wanted = depth_position(room, sun, window_azimuth)
        if wanted is None:
            return max(fixed, self.position) if self.position is not None else fixed
        if wanted != self.position:
            self.position, self.at = wanted, now
        return max(fixed, wanted)
