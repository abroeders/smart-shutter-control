"""The calibration as a table (#40): rows from the stored points and back, and the checks."""

from core.calibration_table import check, data_from, rows_from, slits_from

STORED = {
    "window_height_cm": 140,
    "points": {"up": [[0.34, 0.09], [0.53, 0.3]], "down": [[0.34, 0.01], [0.6, 0.31]]},
    "slit": {"up": 0.2, "down": None},
}


def test_rows_from_the_stored_points():
    assert rows_from(STORED) == [
        {"module": 34, "up": 9, "down": 1},
        {"module": 53, "up": 30},
        {"module": 60, "down": 31},
    ]
    assert slits_from(STORED) == {"up": 20}
    assert rows_from(None) == [] and slits_from({}) == {}


def test_points_from_the_rows_skip_empty_cells():
    rows = [
        {"module": 53, "up": 30},
        {"module": 34, "up": 9, "down": 1},
        {"module": 60, "down": 31, "up": ""},
    ]
    data = data_from(rows, {"up": 20, "down": None}, 140)
    assert data == {
        "window_height_cm": 140,
        "points": {"up": [[0.34, 0.09], [0.53, 0.3]], "down": [[0.34, 0.01], [0.6, 0.31]]},
        "slit": {"up": 0.2},
    }
    assert rows_from(data) == rows_from(STORED)


def test_checks():
    good = [{"module": 30, "up": 5}, {"module": 60, "up": 40, "down": 33}]
    assert check(good) == []
    assert check([{"module": 0, "up": 5}, *good]) == ["module_range"]
    assert check([{"module": 30, "down": 1}, *good]) == ["module_twice"]
    assert check([{"module": 80, "up": 120}, *good]) == ["opening_range"]
    assert check([{"module": 30, "up": 5}, {"module": 60, "down": 33}]) == ["too_few_points"]
    assert check([*good, {"module": 80, "up": 20}]) == ["opening_falls"]
    assert check([]) == ["too_few_points"]
