# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Storm: each wind source has its own limit; in a storm shutters with automatic control are only fully open
  or fully closed, at the end nearest to what the other rules want (locked open by day, closed when the
  evening starts), always closed when the maximum position is below 100 %. A position in between through
  the integration's entities goes to the nearest end, a move by a wall switch is put back within seconds,
  and calibration does not start. The storm ends after a release time (#6).
- Frost: at or below a limit the controller does not move the shutters (#6).
- Optional temperature limits to close in heat or cold (#6).
- Base sensors *Storm* and *Frost*; per shutter the setting *Storm position* (inherited from the base
  schedule) (#6).

### Changed

- The single storm limit of earlier versions becomes the gust limit (#6).

### Fixed

- Holidays from a calendar whose integration starts after this one (e.g. Google Calendar) are read once the
  calendar is available, not only the next night (#20).
- Shutter devices are linked to the base device with `via_device_id` where Home Assistant supports it.

### Changed

- The holidays page has two steps: the calendar first, then its holidays at once, to check the ones to
  ignore (#20).

## [0.3.1] - 2026-11-20

### Added

- Holidays: check boxes to ignore holidays from the calendar; a checked holiday counts as a normal day every
  year, also when its date moves (#20).

### Changed

- The shutter's schedule page is called *Schedule overrides* and shows the base value under each setting,
  instead of one long list in the description (#20).

## [0.3.0] - 2026-11-20

### Added

- Schedules: per shutter a day of phases (night, slit, day, dusk) with weekday and weekend/holiday times,
  sun-relative dusk and closing times with earliest/latest limits, and an optional "not before sunrise". A
  base schedule in the base controller is inherited by every shutter, which can override each setting or
  reset to the base (#4).
- Holidays: public holidays from a calendar entity of Home Assistant's *Holiday* integration, extra dates
  (once or yearly) and excluded dates, edited in the base controller; weekend days are configurable (#4).
- Sleep-in: a switch per shutter and one for all; the shutter stays closed next morning until it is
  operated by hand or the sleep-in end time (#4).
- Manual operation: a move that the controller did not cause pauses automatic control (until the next
  phase, for a while, or not at all). Moving the shutter by hand to the position automatic control wants,
  the *Resume automatic control* button or switching automatic control on resumes it; the button and the
  switch move the shutter at once (#5).
- Entities: *Phase*, *Next action* (filled), *Manual pause*, *Resume automatic control*, *Sleep in*,
  *Sleep in (all shutters)*, *Weekend or holiday* (#4, #5).

- Calibration without a motor power sensor: the assistant measures the travel time first and waits for the
  expected travel of every move; the travel time is a shutter setting that can also be entered by hand (#18).

### Changed

- The controller moves a shutter only when its target changes, not on every tick (#4).

## [0.2.2] - 2026-11-20

### Fixed

- Calibration: moving to closed (and open) is one uninterrupted command, confirmed when the module reports
  the end position and the motor has stopped. Before, a module that reports its position rarely while moving
  was taken for stopped: the command was sent again (the shutter moved in steps) and the assistant went on
  before the shutter was closed (#16).
- Calibration: a stop is detected from the motor power instead of the position reports, and the position
  is read from a report that came after the stop (with a poll), so the shutter no longer stops and starts on
  its way to a measuring point (#16).

### Added

- Optional *Motor power sensor* per shutter; when empty, a power sensor on the shutter's device is used (#16).

## [0.2.1] - 2026-11-20

### Added

- Number *Opening* per shutter: shows the real (calibrated) opening of the window and moves the shutter to
  a value you enter.
- Sensor *State* per shutter: closed, slit (gaps open, bottom bar on the sill), partly open or open.

### Changed

- The calibration assistant first finds where the bottom bar leaves the sill and then measures four points
  spread over the travel above it, in both directions, so no point falls on the sill. A point on the sill
  anyway adds one higher (up) or skips the lower ones (down). The result explains whether the motor is
  equally fast up and down.

### Fixed

- Calibration assistant: a shutter that stopped short of a point (e.g. 13 % instead of 25 % right after
  reaching closed) is sent there again, and the assistant waits for the run-on after an end position.
- A shutter with open slat gaps (opening 0 %) is shown as open, not closed.
- Entering a real position picks the whole module position that comes closest.
- Fully closed and fully open are always the module's end positions (0 and 100), so it runs to its limit
  switches; at module 100 the shutter is shown as fully open in both directions.

## [0.2.0] - 2026-11-20

### Added

- Calibrated positions: per shutter and per direction a roller model (or a monotone curve) from measured
  points, so 50 % is half way down the window from closed and from open. The shutter entity shows the
  calibrated position; attributes `module_position`, `direction`, `calibrated` and `slit` (#10).
- Calibration assistant under *Reconfigure → Calibrate*: moves the shutter, asks for the measured opening,
  finds the point where the bottom bar lifts, shows the result per direction. *Add a calibration point*
  improves a calibration later (#10).
- Diagnostic sensor *Calibration* per shutter (#10).

- Heat protection: a shutter goes down to its shading position when the sun shines on its window (sun
  position against the window direction and tilt, elevation limits), it is sunny (PV power against a learned
  clear-sky reference, falling back to the PV peak power or the weather) and warm (outdoor or room
  temperature). Delays keep passing clouds from moving it (#3).
- Base controller: options page *Sun*, sensors *Sun factor* and *Sunny* (#3).
- Per shutter: *Heat protection* switch, *Shading position*, *Sun on the window* sensor; optional per shutter
  temperature limits (#3).

### Changed

- Rules can now give a target or a cap; caps only lower a shutter (#3).
- *Reconfigure* of a shutter is now a menu: *Settings*, *Calibrate*, *Add a calibration point* (#10).

## [0.1.0] - 2026-11-20

### Added

- Repository scaffold: HACS integration with a minimal config flow, brand icons, CI (#1).
- Base controller with sources (outdoor temperature, weather, PV, wind) and a storm limit; one device per
  shutter, added as a subentry with its window direction, tilt, sun elevation limits and maximum position (#2).
- Per shutter: a shutter entity with its (later calibrated) position, a switch for automatic control, the
  maximum position and sensors for the reason and the next action. No rules yet: nothing moves automatically
  (#2).

[Unreleased]: https://github.com/abroeders/smart-shutter-control/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/abroeders/smart-shutter-control/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/abroeders/smart-shutter-control/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/abroeders/smart-shutter-control/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/abroeders/smart-shutter-control/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/abroeders/smart-shutter-control/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/abroeders/smart-shutter-control/releases/tag/v0.1.0
