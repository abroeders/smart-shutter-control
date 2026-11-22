# The card's "Sun has left the window" button only when the sun lowered the shutter

- Issue: #73
- Status: **approved** (2026-11-22)
- Date: 2026-11-22

## 1. Purpose

The card shows the button *Sun has left the window* whenever the sun is on the window: also in the morning
while the shutter is still in its night position, or while it is open. Pressed then, it records a horizon point
(#54) the user did not intend. The button only helps when the sun lowered the shutter: the user then sees the
sun go behind a building or tree and presses it.

## 2. What the user sees

- The card shows the button only while the shutter's reason is **heat protection** or **glare protection**
  (the *Reason* sensor is `heat` or `glare`): the sun lowered the shutter.
- When the reason is the schedule, the winter rules, a manual pause or anything else, the card shows no button,
  even when the sun is on the window.
- The button entity on the shutter's device does not change: it can still be pressed from there or from an
  automation.

## 3. Behaviour

`frontend/src/viewmodel.ts` gets `showSunLeft(model)`: true when the model has the button entity and its
reason is `heat` or `glare`. `card.ts` uses it in place of the check on *Sun on the window*. The reason already
implies that the sun is on the window, so the card no longer needs that sensor for the button.

## 4. Tests

- `showSunLeft`: true for `heat` and `glare`; false for `schedule`, `winter`, `manual`, `null`; false without
  the button entity.

## 5. Out of scope

How the horizon point is recorded (#54).
