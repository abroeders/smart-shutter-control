# Sun factor at a low sun while the reference is young

- Issue: #107
- Status: **approved** (2026-11-25)
- Date: 2026-11-25

## 1. Purpose

Until the clear-sky reference for a position of the sun is learned, the PV sun factor is measured against a
rough curve from the panels' peak power (`PvBaseline.young_reference`):

```
reference = 0.8 × kWp × 1000 × sin(elevation)
```

The curve only models direct sunlight. With the sun a few degrees above the horizon most PV output is diffuse
light, while `sin(elevation)` makes the reference tiny: about 6 % of the peak power at 4°. A small output under
an overcast sky then gives a sun factor of 100 %, and glare protection lowers shutters on a grey morning.

The user also cannot see how far the reference is learned.

## 2. What the user sees

- Shortly after sunrise and before sunset, on a cloudy day, the sun factor no longer jumps to 100 % and glare
  protection and heat protection stay off.
- On a clear morning with the sun on the window, glare protection works as before.
- The sun factor sensor has two new attributes: `learned_days` (days with data for the current position of the
  sun) and `learned_days_needed` (7). When they are equal, `source` is `learned`.
- Nothing changes once the reference is learned, or with light sensors (lux).

## 3. Behaviour

Only the young PV baseline (`source` = `pv_peak`) changes.

### Diffuse floor

The young reference never drops below its value at **10°** elevation:

```
reference = 0.8 × kWp × 1000 × sin(max(elevation, 10°))
```

At 4° the reference becomes about 14 % of the peak power instead of 6 %. Overcast light at a low sun (a few
percent of the peak) now gives a factor well below the threshold. Above 10° nothing changes.

### Low sun: the weather decides

Below **10°** elevation the PV curve is not reliable in either direction: diffuse light makes it too high under
clouds, and the panels' own tilt and shade can make it too low in clear sun. With a weather entity configured
and the reference young, the sunny state at a low sun follows the weather, as the existing weather fallback
does (`sunny`, `partlycloudy`: sunny; anything else: not sunny). The factor is still computed with the floor and
shown; `source` becomes `pv_peak_weather` so the decision can be traced.

Without a weather entity the floor alone decides.

| Elevation | Reference | Weather entity | Sunny when |
|---|---|---|---|
| ≤ 0° | – | – | never (night, as now) |
| 0–10°, young | floor | yes | weather is `sunny` or `partlycloudy` |
| 0–10°, young | floor | no | factor ≥ threshold (with hysteresis) |
| > 10°, young | curve | – | factor ≥ threshold (as now) |
| learned | learned | – | factor ≥ threshold (as now) |

### Learning progress

`ClearSkyReference.days(sun)` returns the number of days with data in the sky cell of the current sun position
(at most 30). The sun factor sensor shows it as `learned_days`, with `MIN_DAYS` as `learned_days_needed`. The
per-shutter facade detectors (lux) are not shown; they have no sensor of their own.

### Why these numbers

- 10°: below it the diffuse part of clear-sky PV is of the same order as the direct part; above it the
  `sin` curve is a fair first guess. At 10° the floor and the curve meet, so the factor does not jump.
- The weather rule reuses the existing list `SUNNY_WEATHER`, so the meaning of "sunny" stays the same.

## 4. Design

- `core/sunny.py`:
  - `LOW_SUN = 10.0` (degrees).
  - `PvBaseline.young_reference`: `sin(max(elevation, LOW_SUN))`.
  - `SunnyDetector.update`: with a young PV baseline, `0 < elevation < LOW_SUN` and `weather is not None`,
    set `sunny = weather in SUNNY_WEATHER` and `source = "pv_peak_weather"`; the factor is still computed.
    Implemented as a method on the baseline strategy (`low_sun(sun, weather) -> bool | None`, `None` = no
    opinion), so `LuxBaseline` keeps its behaviour (Strategy).
  - `ClearSkyReference.days(sun) -> int`.
- `sensor.py`: `learned_days`, `learned_days_needed` on the sun factor sensor (unrecorded attributes are not
  needed: they change at most once per cell per day).
- Translations: the new `source` value and the attribute names (en, nl).
- `docs/architecture.md`: class diagram of `SunnyDetector` / `PvBaseline` / `ClearSkyReference`; the decision
  table above in the sunny section.
- User docs: `how-it-works.md` (sun factor at a low sun), `entities.md` (new attributes), FAQ ("my shutters
  went down on a grey morning").

## 5. Tests (`tests/test_sun.py`, sensor attributes in `tests_ha/test_sun.py`)

- Young PV, elevation 4°, small output, weather `cloudy`: not sunny, `source` `pv_peak_weather`.
- Same with weather `sunny`: sunny.
- Same without weather: the floor applies; a small output is not sunny, a high output is.
- Young PV at 10° and 30°: the same factor as before.
- Learned reference at 4°: unchanged (no weather rule).
- Lux baseline at 4°: unchanged.
- `days()`: 0 for an unknown cell, the number of days for a known one, never more than 30.

## 6. Out of scope

- Changes to the learned reference (cells, percentile, `MIN_DAYS`).
- A setting for the 10° limit.
- Learning progress of the per-shutter facade light sensors.
