"""The horizon of a window (#54)."""

from core.horizon import Horizon, check, from_rows, rows_from
from core.sun import SunPosition, WindowGeometry

HOUSES = Horizon.from_data([[200, 8], [230, 5], [250, 12]])


def test_between_points_the_horizon_is_interpolated():
    assert HOUSES.elevation_at(215) == 6.5
    assert HOUSES.elevation_at(240) == 8.5
    assert HOUSES.elevation_at(230) == 5


def test_the_outer_points_reach_15_degrees_further():
    assert HOUSES.elevation_at(190) == 8
    assert HOUSES.elevation_at(185) == 8
    assert HOUSES.elevation_at(184) is None
    assert HOUSES.elevation_at(265) == 12
    assert HOUSES.elevation_at(266) is None
    assert Horizon().elevation_at(180) is None


def test_a_new_point_replaces_a_near_one():
    horizon = HOUSES.with_point(231.5, 6.04)
    assert horizon.points == ((200, 8), (231.5, 6.0), (250, 12))
    assert HOUSES.with_point(220, 7).points[1] == (220, 7)


def test_the_window_uses_the_highest_of_horizon_and_lowest_elevation():
    window = WindowGeometry(180, min_elevation=6, horizon=HOUSES)
    assert window.lowest_elevation(SunPosition(230, 3)) == 6  # houses lower than the lowest elevation
    assert window.lowest_elevation(SunPosition(250, 3)) == 12
    assert window.lowest_elevation(SunPosition(120, 3)) == 6  # no points this way
    assert not window.sun_on(SunPosition(245, 9))  # 9° < 10.25°: behind the houses
    assert window.sun_on(SunPosition(225, 9))
    assert window.why_not(SunPosition(245, 9)) == ("below_horizon", {"elevation": 9, "limit": 10.2})


def test_the_table():
    assert rows_from(HOUSES)[0] == {"azimuth": 200, "elevation": 8}
    assert from_rows([{"azimuth": "230", "elevation": 5}, {"azimuth": 200, "elevation": 8}]).points == (
        (200, 8),
        (230, 5),
    )
    assert check([{"azimuth": 200, "elevation": 8}]) == []
    assert check([{"azimuth": 400, "elevation": 8}]) == ["azimuth_range"]
    assert check([{"azimuth": 200, "elevation": 8}, {"azimuth": 200, "elevation": 9}]) == ["azimuth_twice"]
    assert check([{"azimuth": 200, "elevation": 70}]) == ["elevation_range"]
    assert check([{"azimuth": 200}]) == ["elevation_range"]
