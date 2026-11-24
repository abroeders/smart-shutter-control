"""The delayed state shared by heat and glare protection (#95)."""

from core.protection import Phase, ProtectionState

CLOSE, OPEN = 300.0, 1200.0


def started() -> ProtectionState:
    s = ProtectionState()
    s.step(False, False, 0, CLOSE, OPEN)
    return s


def test_first_step_shades_at_once():
    s = ProtectionState()
    assert s.step(True, False, 0, CLOSE, OPEN) is Phase.SHADING and s.active


def test_waits_for_the_close_delay():
    s = started()
    assert s.step(True, False, 10, CLOSE, OPEN) is Phase.PENDING and not s.active
    assert s.remaining(110, CLOSE) == 200
    assert s.step(True, False, 309, CLOSE, OPEN) is Phase.PENDING
    assert s.step(True, False, 310, CLOSE, OPEN) is Phase.SHADING


def test_pending_ends_when_the_conditions_go():
    s = started()
    s.step(True, False, 10, CLOSE, OPEN)
    assert s.step(False, False, 20, CLOSE, OPEN) is Phase.OPEN


def test_waits_for_the_open_delay_and_returns_when_wanted_again():
    s = ProtectionState()
    s.step(True, False, 0, CLOSE, OPEN)
    assert s.step(False, False, 100, CLOSE, OPEN) is Phase.LEAVING and s.active
    assert s.remaining(400, OPEN) == 900
    assert s.step(True, False, 500, CLOSE, OPEN) is Phase.SHADING
    s.step(False, False, 600, CLOSE, OPEN)
    assert s.step(False, False, 1799, CLOSE, OPEN) is Phase.LEAVING
    assert s.step(False, False, 1800, CLOSE, OPEN) is Phase.OPEN


def test_gone_skips_the_open_delay():
    s = ProtectionState()
    s.step(True, False, 0, CLOSE, OPEN)
    assert s.step(False, True, 100, CLOSE, OPEN) is Phase.OPEN


def test_reset_opens_but_keeps_started():
    s = ProtectionState()
    s.step(True, False, 0, CLOSE, OPEN)
    s.reset()
    assert s.phase is Phase.OPEN
    assert s.step(True, False, 10, CLOSE, OPEN) is Phase.PENDING
