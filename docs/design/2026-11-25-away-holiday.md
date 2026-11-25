# Away and holiday

- Issue: #51
- Status: **approved** (2026-11-25)
- Date: 2026-11-25

## 1. Purpose

When nobody is home, the shutters do not have to serve anyone in the rooms: heat can be kept out earlier, and
glare does not matter. On holiday the house should also look lived in: shutters that open and close at exactly
the same minute every day give that away.

## 2. What the user sees

### Base controller settings (options flow)

| Setting | Default | Meaning |
|---|---|---|
| **Presence entity** (optional) | none | a `zone.home`, a `person` or `device_tracker`, a `group`, or a `binary_sensor` |
| **Away after** | 15 min | how long nobody must be home before the house counts as away |
| **Away: heat protection lower by** | 3 °C | both heat thresholds (outdoor and room) are this much lower while away |
| **Holiday: time shift up to** | 30 min | the largest random shift of the schedule times on holiday |

Without a presence entity the house is never away, unless the holiday switch is on.

### Entities on the base controller device

- **Switch *Holiday*** (Dutch *Vakantie*): on = holiday mode. Only switched by the user or an automation; the
  integration never turns it on by itself. Kept across restarts (runtime store, like *Automatic control*).
- **Binary sensor *Away*** (Dutch *Afwezig*, no device class: `presence` would mean the opposite):
  on while the house counts as away (presence entity or holiday). Attribute `since` (when it became away).

### Reason and decision trace

No new reason: a shutter in heat protection still shows `sun`. The decision trace shows:

- heat: the thresholds actually used, with `away: true` when they were lowered;
- glare: `away` as the reason why glare protection does nothing;
- schedule: on holiday the shift of the morning and the evening of today (`shift_morning`, `shift_evening`,
  in minutes).

## 3. Behaviour

### Who is home

The presence entity counts as **home** when:

| Domain | Home when |
|---|---|
| `zone` | the state (number of persons in the zone) is above 0 |
| `person`, `device_tracker` | the state is `home` |
| `group` | the state is `home` or `on` |
| `binary_sensor` | the state is `on` |

`unknown` and `unavailable` count as home (nothing changes when a sensor drops out).

- **Away** starts when the entity has reported nobody home for *Away after* without a break; coming home
  counts **at once**.
- **Holiday** on counts as away at once, whatever the presence entity says.
- A restart does not wait again: when the entity reports nobody home at start, the house counts as away after
  *Away after* from the start (the time of the last change is not reliable across restarts).

### Away

- **Heat protection**: the outdoor and the room threshold are *Away: heat protection lower by* lower, for every
  shutter (also for a shutter with its own thresholds). Default 22/24 °C → 19/21 °C. The hot-day forecast limit
  (#50), the sun and the sunny check are unchanged. The shading position is unchanged.
- **Glare protection** does nothing (as if switched off for the shutter); a shutter lowered for glare goes back
  up through the usual open delay.
- Everything else (schedule, winter, storm, frost, locks, manual operation, doors and windows) is unchanged. In
  cool weather there is no extra shading: winter solar gain stays.
- When the house is no longer away, the usual thresholds apply again at the next evaluation; heat protection
  then ends through its usual open delay, so a shutter does not jump up the moment someone walks in.

### Holiday: presence simulation

- Every schedule time of a shutter is shifted on holiday days: the **morning** (slit and opening) by one random
  shift, the **evening** (dusk and closing) by another, each between −*shift* and +*shift* minutes (uniform,
  whole minutes). Two draws instead of four keep the order of slit → open and dusk → close.
- The shifts differ **per day and per shutter**. They are derived from a random seed that is made once and
  stored (runtime store), the date and the shutter's subentry id, so a restart or a reload gives the same
  shifts for the same day (no shutter going up twice).
- The shift is applied **after** the usual limits (not before sunrise, earliest and latest close), so on
  holiday a shutter may open up to *shift* minutes before sunrise or close up to *shift* minutes after the
  latest close time. The order slit → open → dusk → close is kept: if a shift would put dusk after the
  closing, dusk is dropped for that day, as without a shift.
- The weekday or weekend times follow the calendar as usual; *Sleep-in* is unchanged.
- Holiday also counts as away (above).

## 4. Design

- `core/presence.py` (pure Python):
  - `is_home(domain, state) -> bool` (the table above).
  - `AwayState` (dataclass: `since_nobody: float | None`, `away_since: float | None`; `step(home, holiday,
    now, delay) -> bool`) — the delay and the "at once" on coming home.
  - `ScheduleShift` (Strategy for the schedule times): `NoShift` and `RandomShift(seed, shutter_id, minutes)`
    with `morning(day)` / `evening(day)` in minutes, from `random.Random(f"{seed}:{shutter_id}:{day}")`.
- `core/model.py`: `Inputs.away: bool = False`, `Inputs.holiday: bool = False`; `SunSettings.away_offset`
  (°C, default 3).
- `core/heat.py`: `_warm` uses `heat_outdoor - away_offset` and `heat_room - away_offset` while
  `ctx.inputs.away`; the values in `why` are the thresholds used, plus `away`.
- `core/glare.py`: while `ctx.inputs.away` the rule behaves as when glare protection is off, with
  `why = ("away", {})`.
- `core/schedule.py`: `DaySchedule` takes a `shift: Callable[[], ScheduleShift]` (read per call, so switching
  holiday on or off takes effect at the next evaluation); `transitions(day)` applies `shift.morning(day)` and
  `shift.evening(day)` after the limits.
- `coordinator.py`: reads the presence entity and tracks it; keeps the `AwayState`; `holiday` loaded from and
  saved to the store (global `holiday`), the seed (global `shift_seed`, made with `secrets.randbits` once);
  `set_holiday(on)`; `away` and `holiday` in `Inputs`; a timer for the end of *Away after* (cancelled through
  `entry.async_on_unload`); `away`, `holiday` in the diagnostics (not the presence entity's state or name).
- `controller.py`: passes the shift for its shutter (subentry id) to its `DaySchedule`.
- `const.py`, `options_flow.py`: `presence`, `away_delay`, `away_heat_offset`, `holiday_shift`, with entity
  selector filtered on the four domains.
- `switch.py`: `HolidaySwitch(BaseEntity)`; `binary_sensor.py`: `AwaySensor(BaseEntity)`.
- Translations (en, nl): the options, the switch, the binary sensor, the trace texts.
- Card (`frontend/src/localize.ts` en + nl): glare why `away`, heat with lowered thresholds, the schedule
  shifts.
- `docs/architecture.md`: class diagram (`AwayState`, `ScheduleShift`, `NoShift`, `RandomShift`), Strategy in
  the patterns table, a state diagram (home → nobody home (waiting) → away → home; holiday → away), a sequence
  diagram (presence change → coordinator → tick).
- User docs: `configuration.md` (the four settings), `entities.md` (switch, binary sensor), `how-it-works.md`
  (away, holiday), FAQ ("why did my shutter open 20 minutes early?").
- This design: kept in line with what is built (deviations and later fixes added here, status updated).

## 5. Tests

- `tests/test_presence.py`: `is_home` for each domain and for `unknown`/`unavailable`; away only after the
  delay, a short absence does not count, home at once, holiday at once.
- `tests/test_heat.py`: lowered thresholds while away (shades at 20 °C away, not at home); the hot-day limit
  unchanged.
- `tests/test_glare.py`: no glare protection while away; back to the open delay when it was active.
- `tests/test_schedule.py`: the shifts stay within ±shift; same seed, day and shutter → same shifts; other day
  or other shutter → (usually) different; the order slit → open and dusk → close is kept; no shift without
  holiday.
- `tests_ha/test_away_holiday.py`: the options flow; the presence entity per domain switches *Away* after the
  delay; holiday switch on → *Away* on and shifted times in the trace; restart keeps holiday and gives the same
  shifts; no presence entity → never away.

## 6. Out of scope

- Per-room presence.
- Switching holiday on automatically (calendar, long absence): an automation can do that.
- Extra shading in cool weather while away, or keeping shutters closed during a holiday for security.
- Turning lights on and off.

## 7. As built

- The schedule's decision trace shows `shift_morning` and `shift_evening` whenever holiday is on, also when a
  shift is 0 (with *Holiday: time shift up to* 0, or a draw of 0).
- *Away: heat protection lower by* is a temperature difference: shown in °F as 1.8 × the °C value, without the
  32 offset (`temperature_interval_unit`).
- Diagnostics redact the `presence` option, like the location.
- The base controller's switch has the key `holiday_mode`: the binary sensor `holiday` (weekend or holiday)
  already used `holiday`.
