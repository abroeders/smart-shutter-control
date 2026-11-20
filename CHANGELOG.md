# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/abroeders/smart-shutter-control/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/abroeders/smart-shutter-control/releases/tag/v0.1.0
