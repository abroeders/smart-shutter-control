"""Manual operation during an automatic move (#108): reversal and a stop halfway."""

from core.manual import SETTLE, ManualDetector


def _moving(power: bool = True) -> ManualDetector:
    """A shutter at 100 that the controller sends to 51, with the motor running (with a power sensor)."""
    d = ManualDetector(travel_time=60)
    d.observe(100, False if power else None, 0)
    d.sent(51, 100, 1)
    if power:
        assert not d.observe(None, True, 2)
    return d


def test_reversal_during_an_automatic_move_is_manual():
    d = _moving(power=False)
    assert not d.observe(88, None, 5)
    assert not d.observe(63, None, 10)
    assert d.observe(67, None, 12)  # 16 from the target, it was 12: the user pressed up
    assert d.command is None


def test_jitter_and_the_own_move_are_not_manual():
    d = _moving(power=False)
    for t, position in enumerate((88, 63, 64, 62, 51)):
        assert not d.observe(position, None, 5 + t)


def test_a_move_outside_start_and_target_stays_manual():
    d = _moving(power=False)
    assert d.observe(40, None, 5)  # past the target


def test_stop_halfway_with_a_power_sensor_is_manual_after_settling():
    d = _moving()
    assert not d.observe(63, None, 10)
    assert not d.observe(None, False, 11)  # the motor stops short of the target
    assert d.settling(12) == SETTLE - 1
    assert not d.check(12)
    assert d.settling(11 + SETTLE) == 0
    assert d.check(11 + SETTLE)
    assert d.command is None


def test_a_late_report_of_the_target_is_not_a_stop():
    d = _moving()
    d.observe(63, None, 10)
    d.observe(None, False, 11)
    assert not d.observe(51, None, 13)  # the module reports its final position after the motor
    assert d.settling(20) == 0 and not d.check(20)


def test_a_short_pause_of_the_motor_is_not_a_stop():
    d = _moving()
    d.observe(None, False, 10)
    assert not d.observe(None, True, 11)  # running again
    assert not d.check(20)


def test_without_a_power_sensor_a_stop_is_left_to_the_arrival_check():
    d = _moving(power=False)
    d.observe(63, None, 10)
    assert d.settling(100) == 0 and not d.check(100)


def test_a_motor_that_never_started_is_left_to_the_arrival_check():
    d = ManualDetector(travel_time=60)
    d.observe(100, False, 0)
    d.sent(51, 100, 1)
    assert not d.observe(None, False, 20)
    assert not d.check(40)
