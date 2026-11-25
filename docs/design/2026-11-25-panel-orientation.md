# Young PV reference: panel orientation and the weather

- Issue: #110 (follow-up of #107)
- Status: **approved** (2026-11-25)
- Date: 2026-11-25

## 1. Purpose

While the clear-sky PV reference for a position of the sun is young, the sun factor compares the PV power with
a rough curve, `0.8 × kWp × 1000 × sin(max(elevation, 10°))` (#107). That curve models **horizontal** panels.
Tilted panels catch a low winter sun far better: panels at 35° facing south, with the sun at 11° elevation and
146° azimuth, get about 3× the irradiance of a horizontal surface. The reference is far too low, the sun factor
hits 100 % under a grey sky, and glare protection lowers the shutters. The weather rule of #107 only applies
below 10°.

## 2. What the user sees

- Two new optional settings in the PV step of the base controller, next to *PV peak power*:
  - **Panel tilt**: degrees from horizontal (0 = flat, 90 = vertical), default **35**.
  - **Panel direction**: azimuth in degrees (0 = north, 90 = east, 180 = south, 270 = west), default **180**.
- While the reference is young, the sun factor fits the panels: realistic values in winter, morning and evening.
- While the reference is young and a weather entity is set, a cloudy, rainy or foggy sky never counts as bright
  sun, at any sun elevation.
- Nothing changes with a learned reference or with light sensors.

## 3. Behaviour

### Young reference with the panel orientation

```
cos_i     = cos(angle of incidence of the sun on the panels)     (as WindowGeometry.incidence)
reference = 0.8 × kWp × 1000 × max(cos_i, sin 10°)
```

- `max(…, sin 10°)` is the diffuse floor of #107, now on the panel: the reference never drops to (almost)
  zero, also not when the sun is low or behind the panels.
- With tilt 0 the formula is the one of #107 (`cos_i = sin(elevation)`), so flat panels behave as before.
- No air-mass correction: at a low sun the reference is somewhat high, so the factor errs towards "not bright".
  Real clear sun still reaches the threshold (example below), and the weather veto covers the rest.

Example (2.6 kWp, 35° south, sun 11° / 146°): `cos_i` ≈ 0.62, reference ≈ 1290 W. This morning's 707 W gives
55 % instead of 100 %; clear sun (about 1000 W) gives about 77 %.

### The weather while young

| Sun elevation | Weather entity | Sunny when |
|---|---|---|
| below 10° | yes | the weather is `sunny` or `partlycloudy` (as #107) |
| 10° and higher | yes | the factor reaches the threshold **and** the weather is `sunny` or `partlycloudy` |
| any | no | the factor reaches the threshold |

`source` is `pv_peak_weather` below 10° (the weather decides) and from 10° when the weather vetoed bright sun,
else `pv_peak`. A learned reference and
light sensors ignore the weather, as now.

### Defaults and existing installations

The new keys are optional. An installation without them uses 35° and 180°; no migration step. Panel tilt and
direction are shown and stored only with the PV sun source; they are removed with the other PV keys when the
sun source changes to light sensors (`SUN_KEYS`).

## 4. Design

- `const.py`: `CONF_PV_TILT = "pv_tilt"`, `CONF_PV_AZIMUTH = "pv_azimuth"`, `DEFAULT_PV_TILT = 35`,
  `DEFAULT_PV_AZIMUTH = 180`.
- `flow_common.py`: both fields in `SUN_FIELDS["pv"]` after `CONF_PV_PEAK` (number selectors: tilt 0–90,
  direction 0–359, step 1, unit °), and in `SUN_KEYS`.
- `core/sunny.py`:
  - `PvBaseline` gets `tilt` and `azimuth`; `young_reference` uses
    `max(WindowGeometry(azimuth, tilt).incidence → cos, sin LOW_SUN)`.
  - `PvBaseline.low_sun(sun, weather)` becomes `weather_rule(sun, weather, sunny_by_factor) -> bool | None`:
    below `LOW_SUN` the weather decides; from `LOW_SUN` a not-sunny weather vetoes; `None` without a weather
    entity. `LuxBaseline.weather_rule` returns `None` (Strategy, as now).
- `coordinator.py`: `PvBaseline(peak, tilt, azimuth)` from the sources, with the defaults.
- Translations (strings, en, nl): labels and descriptions of the two fields in the PV step (setup and options).
- `docs/architecture.md`: the `PvBaseline` class (new fields, `weather_rule`) and the text of section 11.
- User docs: `configuration.md` (two rows in the PV table), `how-it-works.md` (young reference, weather), FAQ
  (the grey-morning answer extended).

## 5. Tests

- `tests/test_sun.py`:
  - tilt 0 gives the reference of #107; tilt 35 south at 11° / 146° gives ≈ 0.62 × 2080 W;
  - sun behind the panels (north): the floor;
  - weather `cloudy` at 30° with a factor of 100 %: not sunny, `source` `pv_peak_weather`; `sunny`: sunny;
  - no weather entity: the factor decides; learned reference and lux: unchanged.
- `tests_ha/test_config_flow.py`: the PV step shows and stores tilt and direction; defaults when left empty;
  switching to light sensors removes them.

## 6. Out of scope

- Several panel arrays with different orientations.
- An air-mass (atmosphere) correction.
- Changes to the learned reference.
