# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and since 2026.11.0 versions follow Home Assistant's scheme: `YEAR.MONTH.N` (before that: 0.1.0–0.6.1).

## [Unreleased]

## [2026.11.14] - 2026-11-22

### Added

- Heat protection from the weather forecast: with *Hot day from (forecast)* (default 28 °C, per shutter
  adjustable), on a day whose forecast maximum reaches it heat protection no longer waits for the outdoor or
  room temperature and lowers a sun-facing shutter as soon as the sun is on the window and it is sunny. New
  base entities *Forecast maximum* and *Hot day* (#50).

### Fixed

- Temperatures and wind speeds in any unit: sensors in °F or mph (and a weather forecast in °F) are converted
  to °C and km/h when read, so frost, storm, heat protection and the temperature limits decide correctly with
  US customary units. The settings stay in °C and km/h (#64).

### Changed

- Releases are published by a workflow, only when the tagged commit passes the HACS and hassfest validation
  and its versions match the tag (#63).

## [2026.11.13] - 2026-11-21

### Added

- Window and door contacts: with an *opened* contact, automatic control raises the shutter to the lockout
  position (fully open by default) and never lowers it below that while the door is open, also not in a
  storm, so nobody is locked out; with a *tilted* contact it keeps at least the ventilation position (the
  slit by default). One minute after the contact closes, the shutter follows its rules again; the reason
  is *lockout* or *ventilation* (#49).

### Changed

- The manifest lists the categories *Blinds & curtains* and *Climate*, and the HACS check runs without
  ignored checks (#61).

## [2026.11.12] - 2026-11-21

### Added

- Moves are checked: when a shutter did not reach the position that was sent (a lost radio command, a module
  that stopped short), the command is sent once more; if that fails too, the binary sensor *Stuck* turns on
  and a repair issue appears, both clearing at the next move that arrives (#48).
- A switch *Automatic control (all shutters)* on the base controller pauses the whole integration: no shutter
  moves by itself, not even in a storm, and the reason is *paused*. Switched on again, every shutter goes to
  its wanted position at once (#53).

## [2026.11.11] - 2026-11-21

### Added

- Shading position from the sun: with the window's height above the floor, its height and how far direct sun
  may reach into the room, heat and glare protection lower the shutter only as far as needed (in steps of
  10 %, at most once per quarter of an hour, never below the fixed position), so a high sun leaves more
  daylight (#55).
- Horizon per window: buildings and trees block a low sun at different heights in different directions.
  The button *Sun has left the window* (also in the card) records the sun's direction and elevation as a
  horizon point, and *Reconfigure → Horizon* shows the points as a table. Heat and glare protection stop when
  the sun is below the horizon (#54).
- Why the shutter is where it is: the *Reason* sensor's attribute `decision` lists what every rule said (the
  position it proposed and whether it decided, or why it did nothing, with the values), and the card unfolds
  it under **Why?** (#56).

## [2026.11.10] - 2026-11-21

### Added

- A Buy Me a Coffee button in the README and a *Sponsor* link on GitHub, for those who want to support the
  project (#57).

## [2026.11.9] - 2026-11-21

### Fixed

- Fully open and fully closed are sent as the module's open and close (its arrows) instead of position
  100 and 0, so the module runs until it stops at its limit switch. A module whose travel-time estimate
  had drifted stopped short of fully open (#46).

## [2026.11.8] - 2026-11-21

### Changed

- Card: only the blue grip on the bottom bar drags the shutter to a position. Touching or scrolling over
  the rest of the drawing on a phone no longer moves the shutter (#44).

## [2026.11.7] - 2026-11-21

### Fixed

- Calibration assistant: it sometimes kept waiting for a position the shutter had reached long before,
  because the module did not report it. While waiting, the assistant now also asks the module for its
  position every 5 seconds, and goes on as soon as the target is reported with the motor stopped (#42).

## [2026.11.6] - 2026-11-21

### Added

- Calibration: *Calibrate* offers the assistant or a table. The table shows the measured points (a row per
  module position, the opening going up and going down) and the slit per direction, filled in with the stored
  calibration; edited rows are checked, the result is shown, and confirming saves it (#40).

## [2026.11.5] - 2026-11-21

### Fixed

- Settings changed through entities (switches such as *Glare protection* and *Heat protection*, positions,
  maximum position) and the learned data were lost when the integration was reloaded: the learned data,
  updated every minute, kept postponing the save. Settings are now saved within seconds, and everything is
  written when the integration unloads (#38).
- After a restart or reload, heat and glare protection act at once when their conditions already hold,
  instead of opening the shutter for the close delay first (#38).

## [2026.11.4] - 2026-11-21

### Added

- Glare protection: per shutter a switch *Glare protection* (off by default), *Glare position* and *Glare
  from*. Bright sun on this window (sun factor at or above the limit, the window's direction and sun
  elevations) during the day phase lowers the shutter to the glare position, whatever the temperature and
  also in winter. New reason *Glare*; attribute `glare_phase` on *Sun on the window* (#36).

## [2026.11.3] - 2026-11-21

### Added

- Card: every window direction has its own landscape and light on the sun's side, and a dotted arc shows
  today's path of the sun through the window (#34).
- Card: the amount of clouds follows the cloud cover; by day the measured light (PV power, light sensors or
  the facade light sensor) weighs three times as much as the weather entity. A sun that is in view but not
  bright has a cloud in front of it that slides aside when the sun breaks through (#34).
- Attribute `cloud_coverage` on *Sun factor*: the weather entity's cloud coverage (#34).

### Changed

- Card: the sun stays visible, dimmed, under a closed cloud layer; a station reporting *cloudy* while the
  panels measure sunshine no longer turns the view grey (#34).
- Help text of *Sunny from* and the documentation: light sensors (lux) as the sun source next to PV power
  (#26).

## [2026.11.2] - 2026-11-20

### Added

- Card: the view through the window. A cartoon landscape with the real light, weather (clouds, rain, snow,
  fog, lightning), the sun and the moon with its phase at their place as seen through the window, leaves by
  season, and trees that sway with the wind, harder in a storm. Fully closed nothing shows; otherwise through
  the slots and below the bottom bar (#30).
- Attributes for the card: `window_azimuth` and `window_tilt` on *Sun on the window*, `weather` on *Sun
  factor*, `wind` and `gust` on *Storm* (#30).

## [2026.11.1] - 2026-11-20

### Fixed

- Card: the drawing shows the gaps between the slats whenever the shutter is not fully closed, also in the
  slit position; fully closed it shows them pressed together (#28).

## [2026.11.0] - 2026-11-20

### Added

- Light sensors (lux) as the sun source, instead of PV power: a select *Sun source* (PV, light sensors,
  none) with a second page for the chosen source only, so both are never set. The highest light sensor
  counts; a learned clear-sky reference per position of the sun, with a fixed limit (30 000 lx) while it is
  young. The page shows each sensor's 30-day maximum and warns when it probably saturates. Optional facade
  light sensor per shutter (#26).

### Changed

- Versions follow Home Assistant's scheme from now on: `2026.11.0`.
- Clearing an optional field in a shutter's settings now removes it.

## [0.6.1] - 2026-11-20

### Added

- Documentation: installation, configuration (every setting with its default and effect), calibration,
  entities, how it works, the card, FAQ and troubleshooting; README with screenshots for HACS (#8).

### Removed

- The source *PV forecast sensor*: it had no function. An existing setting is removed at start-up.

## [0.6.0] - 2026-11-20

### Added

- Lovelace card *Smart Shutter*, served by the integration: a drawing of the shutter at its real position
  that you can drag (or move with the keyboard), open/stop/close, the reason and the next two actions,
  *Automatic*, *Sleep in* and *Resume*; with the base controller as device, all shutters as tiles. During a
  storm the drag goes only to fully open or closed (#9).
- *Configure → Language*: system language, English or Nederlands for the card and the entity names (#9).
- Sensor *Next action*: attribute `following` with the two changes after the next one; the shutter's cover
  reports *opening* and *closing* while it moves (#9).

## [0.5.0] - 2026-11-20

### Added

- Winter mode: on while the 24-hour mean outdoor temperature is below a limit (select *Winter mode*: auto, on,
  off). In winter a shutter stays closed all day at or below a temperature (default −5 °C; a manual action
  overrides it), and the dusk position never raises a closed shutter. Per shutter on/off and limit, inherited
  from the base schedule. Sensor *Winter* with the 24-hour mean (#7).

### Changed

- *Schedule overrides*: the choice fields show *Inherit* when the shutter follows the base schedule, also
  after *Reset to the base schedule*; *After a manual action* can now be inherited too.

## [0.4.0] - 2026-11-20

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

[Unreleased]: https://github.com/abroeders/smart-shutter-control/compare/2026.11.14...HEAD
[2026.11.14]: https://github.com/abroeders/smart-shutter-control/compare/2026.11.13...2026.11.14
[2026.11.13]: https://github.com/abroeders/smart-shutter-control/compare/2026.11.12...2026.11.13
[2026.11.12]: https://github.com/abroeders/smart-shutter-control/compare/2026.11.11...2026.11.12
[2026.11.11]: https://github.com/abroeders/smart-shutter-control/compare/2026.11.10...2026.11.11
[2026.11.10]: https://github.com/abroeders/smart-shutter-control/compare/2026.11.9...2026.11.10
[2026.11.9]: https://github.com/abroeders/smart-shutter-control/compare/2026.11.8...2026.11.9
[2026.11.8]: https://github.com/abroeders/smart-shutter-control/compare/2026.11.7...2026.11.8
[2026.11.7]: https://github.com/abroeders/smart-shutter-control/compare/2026.11.6...2026.11.7
[2026.11.6]: https://github.com/abroeders/smart-shutter-control/compare/2026.11.5...2026.11.6
[2026.11.5]: https://github.com/abroeders/smart-shutter-control/compare/2026.11.4...2026.11.5
[2026.11.4]: https://github.com/abroeders/smart-shutter-control/compare/2026.11.3...2026.11.4
[2026.11.3]: https://github.com/abroeders/smart-shutter-control/compare/2026.11.2...2026.11.3
[2026.11.2]: https://github.com/abroeders/smart-shutter-control/compare/2026.11.1...2026.11.2
[2026.11.1]: https://github.com/abroeders/smart-shutter-control/compare/2026.11.0...2026.11.1
[2026.11.0]: https://github.com/abroeders/smart-shutter-control/compare/v0.6.1...2026.11.0
[0.6.1]: https://github.com/abroeders/smart-shutter-control/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/abroeders/smart-shutter-control/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/abroeders/smart-shutter-control/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/abroeders/smart-shutter-control/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/abroeders/smart-shutter-control/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/abroeders/smart-shutter-control/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/abroeders/smart-shutter-control/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/abroeders/smart-shutter-control/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/abroeders/smart-shutter-control/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/abroeders/smart-shutter-control/releases/tag/v0.1.0
