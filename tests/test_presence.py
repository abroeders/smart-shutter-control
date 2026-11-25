"""Away and holiday (#51): who is home and the away delay."""

import pytest
from core.presence import AwayState, is_home

DELAY = 900.0


@pytest.mark.parametrize(
    ("domain", "state", "home"),
    [
        ("zone", "2", True),
        ("zone", "0", False),
        ("person", "home", True),
        ("person", "not_home", False),
        ("person", "work", False),
        ("device_tracker", "home", True),
        ("device_tracker", "not_home", False),
        ("group", "home", True),
        ("group", "on", True),
        ("group", "not_home", False),
        ("group", "off", False),
        ("binary_sensor", "on", True),
        ("binary_sensor", "off", False),
    ],
)
def test_is_home_per_domain(domain, state, home):
    assert is_home(domain, state) is home


@pytest.mark.parametrize("domain", ["zone", "person", "device_tracker", "group", "binary_sensor"])
@pytest.mark.parametrize("state", ["unknown", "unavailable", None])
def test_unknown_and_unavailable_count_as_home(domain, state):
    assert is_home(domain, state) is True


def test_away_only_after_the_delay():
    s = AwayState()
    assert s.step(False, False, 1000, DELAY) is False
    assert s.step(False, False, 1000 + DELAY - 1, DELAY) is False
    assert s.remaining(1000 + DELAY - 1, DELAY) == 1
    assert s.step(False, False, 1000 + DELAY, DELAY) is True
    assert s.away_since == 1000 + DELAY and s.remaining(5000, DELAY) is None


def test_a_short_absence_does_not_count():
    s = AwayState()
    s.step(False, False, 0, DELAY)
    assert s.step(True, False, 600, DELAY) is False and s.nobody_since is None
    s.step(False, False, 700, DELAY)
    assert s.step(False, False, 700 + DELAY - 1, DELAY) is False  # the delay starts again


def test_coming_home_counts_at_once():
    s = AwayState()
    s.step(False, False, 0, DELAY)
    assert s.step(False, False, DELAY, DELAY) is True
    assert s.step(True, False, DELAY + 1, DELAY) is False and s.away_since is None


def test_holiday_is_away_at_once_and_keeps_the_house_away_when_home():
    s = AwayState()
    assert s.step(True, True, 100, DELAY) is True and s.away_since == 100
    assert s.step(True, True, 200, DELAY) is True and s.away_since == 100
    assert s.step(True, False, 300, DELAY) is False and s.away_since is None


def test_a_zero_delay_is_away_at_once():
    assert AwayState().step(False, False, 5, 0) is True
