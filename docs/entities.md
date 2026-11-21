# Entities

Names follow the integration's *Language* setting (or Home Assistant's system language).

## Base controller

| Entity | Shows or does |
|---|---|
| sensor *Sun factor* | PV power or illuminance as % of its learned clear-sky value for this position of the sun; attributes `source` (`learned`, `pv_peak`, `lux_learned`, `lux_limit`, `weather`, `geometry`), `sun_source`, `weather`, `cloud_coverage` (%, from the weather entity, for the card), `lux`, `sun_azimuth`, `sun_elevation` |
| binary_sensor *Sunny* | sun factor above the threshold (with hysteresis) |
| binary_sensor *Weekend or holiday* | today uses the weekend times; attribute `holiday` (its name) |
| binary_sensor *Storm* | storm (see [How it works](how-it-works.md#storm)) |
| binary_sensor *Frost* | frost: no automatic moves |
| binary_sensor *Winter* | winter mode active; attributes `mean_24h`, `mode` |
| select *Winter mode* | *Auto* (by the 24-hour mean), *On*, *Off* |
| switch *Sleep in (all shutters)* | turns sleep-in on or off for every shutter |

## Each shutter

| Entity | Shows or does |
|---|---|
| cover *Shutter* | the real (calibrated) position; open, close, stop and set position act as a manual action. *Opening*/*closing* while it moves. Attributes `module_position`, `direction`, `calibrated`, `slit` |
| number *Opening* | the real opening in %; setting it moves the shutter there (manual, ignores the maximum position) |
| number *Maximum position* | automatic control never opens the shutter further |
| number *Shading position* | position during heat protection |
| switch *Automatic control* | off: the integration does not move this shutter; on: it moves to the wanted position at once |
| switch *Heat protection* | heat protection for this shutter |
| switch *Sleep in* | stays closed in the coming slit and day phases; ends on a manual action or at *Sleep in until* |
| button *Resume automatic control* | ends a manual pause and moves the shutter to the wanted position |
| sensor *Reason* | why the shutter is where it is: idle, automatic control off, manual, calibrating, sun, schedule, sleep in, storm, frost, heat limit, cold limit, winter. Attributes `target_position`, `max_position`, `language` |
| sensor *Next action* | time of the next phase change; attributes `phase`, `position`, `following` (the two after it), `overrides` |
| sensor *Phase* | night, slit, day or dusk |
| sensor *State* | closed, slit (gaps open, bar on the sill), partly open, open; attributes `opening`, `module_position` |
| sensor *Calibration* (diagnostic) | calibrated or not; the points, the model and the fit per direction |
| binary_sensor *Sun on the window* | the sun is in front of the window and not blocked (geometry only); attribute `incidence`; with a facade light sensor also `sunny`, `sun_factor`, `lux`, `source` |
| binary_sensor *Manual pause* | automatic control is paused after a manual action; attributes `since`, `until`, `source` |
