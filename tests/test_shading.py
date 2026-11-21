"""The shading position from the sun (#55)."""

from core.shading import HOLD, DepthShading, RoomGeometry, depth_position
from core.sun import SunPosition

ROOM = RoomGeometry(sill_cm=50, window_cm=150, depth_m=1.0)


def test_a_high_sun_needs_little_shade_and_a_low_sun_much():
    # 45° straight on: light through an opening o reaches (50 + o) cm: o = 50 cm, a third of the window
    assert depth_position(ROOM, SunPosition(180, 45), 180) == 30
    # 60°: tan 60° · 100 − 50 = 123 cm → 82 % → 80 %
    assert depth_position(ROOM, SunPosition(180, 60), 180) == 80
    # 25°: tan 25° · 100 < 50 cm: the sill alone lets the sun in further, so closed
    assert depth_position(ROOM, SunPosition(180, 25), 180) == 0


def test_a_sun_at_an_angle_reaches_less_far_into_the_room():
    # γ = 60°: tan φ = tan 30° / cos 60° = 1.155 → o = 65 cm → 43 % → 40 %
    assert depth_position(ROOM, SunPosition(240, 30), 180) == 40
    assert depth_position(ROOM, SunPosition(180, 30), 180) == 0
    assert depth_position(ROOM, SunPosition(275, 30), 180) is None  # behind the wall


def test_never_below_the_fixed_position_and_steps_held_for_a_quarter():
    shade = DepthShading()
    assert shade(0, ROOM, SunPosition(180, 60), 180, 90, fixed=30) == 80
    assert shade(60, ROOM, SunPosition(180, 45), 180, 90, fixed=30) == 80  # held
    assert shade(HOLD, ROOM, SunPosition(180, 45), 180, 90, fixed=30) == 30
    assert shade(2 * HOLD, ROOM, SunPosition(180, 20), 180, 90, fixed=30) == 30  # 0 % wanted: the fixed one
    shade.reset()
    assert shade(2 * HOLD + 1, ROOM, SunPosition(180, 60), 180, 90, fixed=30) == 80  # at once after a reset


def test_without_geometry_or_on_a_sloped_window_the_fixed_position():
    shade = DepthShading()
    assert shade(0, None, SunPosition(180, 60), 180, 90, fixed=30) == 30
    assert shade(0, ROOM, SunPosition(180, 60), 180, 30, fixed=30) == 30


def test_heat_protection_follows_the_sun_with_a_room_geometry():
    from core.heat import HeatProtectionRule, SunSettings
    from core.model import Inputs, ShutterConfig, ShutterContext

    def ctx(now, sun):
        config = ShutterConfig("cover.a", 180, room=ROOM)
        return ShutterContext(
            config,
            Inputs(now=now, outdoor=28.0, sun=sun, sunny=True),
            100,
            100,
            heat_protection=True,
            shading_position=20,
        )

    heat = HeatProtectionRule(SunSettings(close_delay=0))
    assert heat.propose(ctx(0, SunPosition(180, 60))).position == 80
    assert heat.propose(ctx(HOLD, SunPosition(180, 45))).position == 30
    assert heat.propose(ctx(2 * HOLD, SunPosition(180, 30))).position == 20  # never below the fixed one
