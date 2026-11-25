# Manual operation during an automatic move

- Issue: #108
- Status: **approved** (2026-11-25)
- Date: 2026-11-25

## 1. Purpose

While its own command runs, `ManualDetector` counts every reported module position between the start and the
target (± `MARGIN`) as part of that command (`_on_the_way`). It ignores the direction of travel. A user who
reverses or stops the shutter during an automatic move is not detected as long as the shutter stays in that
range: no manual pause starts, and the arrival check (#48) sends the target again.

Observed: the controller sends 100 → 51; reports 88, 63, **67** (the user presses up), 55, 51.

Stopping or reversing an automatic move is the moment a user most often wants to override it.

## 2. What the user sees

- Pressing the switch against the direction of an automatic move: the shutter does what the user wants, the
  manual pause starts (with the configured manual mode), and the controller does not send its target again.
- Stopping an automatic move halfway (shutters with a power sensor): the same.
- Automatic moves that run normally are never taken for manual ones.

## 3. Behaviour

### Reversal

The active command remembers the smallest distance to its target seen so far (`closest`, starting at the start
position's distance). A report counts as manual when it is **further from the target than `closest` + `MARGIN`**.

| Report | Distance to 51 | `closest` | Manual? |
|---|---|---|---|
| 88 | 37 | 37 | no |
| 63 | 12 | 12 | no |
| 67 | 16 | 12 | **yes** (16 > 12 + 2) |

The existing range check (`_on_the_way`) stays: a report outside start…target (overshoot, other side) is still
manual.

### Stop halfway (with a power sensor)

When the motor of a started command stops while the module is more than `MATCH` from the target, and no new
position comes within a short settle time (**5 s**, the existing `END_SETTLE`), the stop counts as manual.

A stop and a blocked shutter (ice, obstacle, motor protection) look the same. The case #48 was built for, a
command the module did not carry out (the motor never starts or the position does not change), stays with the
arrival check: retry once, then stuck. A move that started and stopped halfway is far more often a hand on the
switch than a blockage.

### Without a power sensor

A stop halfway cannot be told from a slow report. Only reversal is detected; a stop stays with the arrival
check as now.

### On a manual action

As today (`Controller._manual`, source `switch`): the command is dropped, the arrival check is cancelled
(`arrival.cancel()`, so no retry), the sent position is forgotten, and the manual pause starts.

### No false positives

- Jitter and late reports within `MARGIN` (2 %) of `closest`: not manual.
- The run-on to an end position: the position does not move away from the target.
- A new automatic command during a move: `sent()` starts a new `ActiveCommand` from the current position.
- The calibration assistant: its moves go through the paused controller as now and are not judged.

## 4. Design

- `core/manual.py`:
  - `ActiveCommand.closest: int | None` (distance to target), set in `sent()` from `start`, updated in
    `observe()`.
  - `ManualDetector.observe`: reversal check next to `_on_the_way`; stop-halfway check when `motor` goes from
    running to idle on a started command away from the target (keeps `stopped_at`); judged in `observe` or in a
    new `check(now)` once the settle time has passed, so the controller's existing arrival timer can call it.
- `controller.py`: call `detector.check(now)` from `async_check_arrival` before judging arrival; when it reports
  manual, call `_manual(now, "switch")` and skip the arrival verdict.
- `docs/architecture.md`: state diagram of `ManualDetector` (idle → command → arrived / manual) and the
  sequence diagram of a manual action during a move.
- User docs: `how-it-works.md` (manual operation), FAQ ("I moved the shutter but it went back").

## 5. Tests (new `tests/test_manual.py`, controller in `tests_ha/test_control.py`)

- 100 → 51 with reports 88, 63, 67: manual at 67.
- Same with jitter 63, 64, 62, 51: not manual.
- Power sensor: motor stops at 63 for 5 s: manual; motor stops at 63 and 51 arrives within 5 s: not manual.
- No power sensor: stop at 63: not manual (arrival check retries as now).
- Motor never starts: not manual, arrival check retries, then stuck (as #48).
- Controller: after a reversal the pause is on and the arrival check does not send the target again.

## 6. Out of scope

- Manual actions while the shutter is at rest (already detected).
- Events from wall switches or module scenes.
- Changes to the manual modes or the pause duration.
