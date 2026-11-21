"""Window and door contacts: lockout and ventilation floors (#49)"""

from core.contacts import HOLD, OpeningGuard, raise_to

SLIT = 12


def floor_of(guard, now=0, max_position=100):
    return guard.floor(now, SLIT, max_position)


def test_no_contact_no_floor():
    guard = OpeningGuard()
    assert floor_of(guard) is None
    assert raise_to(("real", 0), ("real", 50), None, False) == ("real", 0)


def test_lockout_raises_a_lower_target_and_leaves_a_higher_one():
    guard = OpeningGuard(lockout=80)
    assert guard.update(True, False, 0)  # just opened
    floor = floor_of(guard)
    assert floor.reason == "lockout" and floor.safety
    assert raise_to(("real", 30), ("real", 100), floor, False) == ("real", 80)
    assert raise_to(("module", SLIT), ("real", 100), floor, False) == ("real", 80)
    assert raise_to(("real", 90), ("real", 100), floor, False) == ("real", 90)


def test_without_a_target_the_current_position_is_raised():
    floor = floor_of(_opened())
    assert raise_to(None, ("real", 0), floor, False) == ("real", 100)
    assert raise_to(None, ("real", 100), floor, False) is None
    assert raise_to(None, None, floor, False) is None


def test_lockout_in_a_storm_is_fully_open():
    guard = OpeningGuard(lockout=60)
    guard.update(True, False, 0)
    assert raise_to(("real", 0), ("real", 100), floor_of(guard), True) == ("real", 100)
    assert raise_to(("real", 100), ("real", 0), floor_of(guard), True) == ("real", 100)


def test_lockout_ignores_the_maximum_position():
    assert floor_of(_opened(), max_position=40).target == ("real", 100)


def test_ventilation_by_the_slit():
    guard = OpeningGuard()
    guard.update(False, True, 0)
    floor = floor_of(guard)
    assert floor.reason == "ventilation" and not floor.safety
    assert raise_to(("real", 0), ("real", 50), floor, False) == ("module", SLIT)
    assert raise_to(("module", SLIT), ("real", 0), floor, False) == ("module", SLIT)
    assert raise_to(("real", 5), ("real", 0), floor, False) == ("real", 5)


def test_ventilation_by_a_percentage_within_the_maximum_position():
    guard = OpeningGuard(ventilation=50)
    guard.update(False, True, 0)
    assert raise_to(("real", 20), None, floor_of(guard), False) == ("real", 50)
    assert floor_of(guard, max_position=30).target == ("real", 30)


def test_ventilation_gives_way_to_a_storm():
    guard = OpeningGuard()
    guard.update(False, True, 0)
    assert raise_to(("real", 0), ("real", 100), floor_of(guard), True) == ("real", 0)


def test_opened_and_tilted_is_lockout():
    guard = OpeningGuard()
    guard.update(True, True, 0)
    assert floor_of(guard).reason == "lockout"


def test_the_floor_holds_a_minute_after_closing():
    guard = _opened()
    assert not guard.update(False, False, 100)
    assert guard.release_at() == 100 + HOLD
    assert floor_of(guard, now=100 + HOLD - 1) is not None
    assert floor_of(guard, now=100 + HOLD) is None
    assert guard.update(True, False, 120)  # opened again within the hold
    assert guard.release_at() is None


def test_unavailable_keeps_the_last_state():
    guard = _opened()
    assert not guard.update(None, None, 10)
    assert floor_of(guard, now=1000).reason == "lockout"
    assert not guard.update(True, False, 20)  # still open: not "just opened"


def _opened() -> OpeningGuard:
    guard = OpeningGuard()
    guard.update(True, False, 0)
    return guard
