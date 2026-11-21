"""Did a move arrive? (#48)"""

from core.arrival import DEFAULT_TRAVEL, EARLIEST, ArrivalCheck, State, Verdict, deadline_for


def test_with_a_power_sensor_due_when_the_motor_stops():
    check = ArrivalCheck(travel=20)
    check.sent(100, 0)
    assert not check.due(False, 5)  # not before the module could start
    assert not check.due(True, 12)  # running
    assert check.due(False, 25)
    assert check.judge(99) is Verdict.ARRIVED and check.state is State.IDLE


def test_a_motor_that_never_starts_is_due_after_the_earliest_moment():
    check = ArrivalCheck(travel=20)
    check.sent(40, 0)
    assert check.due(False, EARLIEST)


def test_without_a_power_sensor_only_the_deadline():
    check = ArrivalCheck(travel=20)
    check.sent(40, 0)
    assert deadline_for(20) == 60
    assert not check.due(None, 59)
    assert check.due(None, 60)
    assert ArrivalCheck().deadline == DEFAULT_TRAVEL


def test_retry_once_then_stuck_and_a_new_command_starts_again():
    check = ArrivalCheck(travel=20)
    check.sent(100, 0)
    assert check.judge(64) is Verdict.RETRY and check.state is State.RETRYING
    check.sent(100, 30)  # the retry
    assert check.state is State.RETRYING
    assert check.judge(64) is Verdict.STUCK and check.state is State.STUCK and not check.due(False, 100)
    check.sent(0, 200)  # the next command
    assert check.state is State.WAITING
    assert check.judge(2) is Verdict.ARRIVED


def test_a_manual_move_cancels():
    check = ArrivalCheck()
    check.sent(50, 0)
    check.cancel()
    assert not check.due(None, 1000)
    check.sent(50, 0)
    check.judge(10)
    check.sent(60, 1)  # another target during the retry: a new check
    assert check.state is State.WAITING
