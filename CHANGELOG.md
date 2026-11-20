# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Repository scaffold: HACS integration with a minimal config flow, brand icons, CI (#1).
- Base controller with sources (outdoor temperature, weather, PV, wind) and a storm limit; one device per
  shutter, added as a subentry with its window direction, tilt, sun elevation limits and maximum position (#2).
- Per shutter: a shutter entity with its (later calibrated) position, a switch for automatic control, the
  maximum position and sensors for the reason and the next action. No rules yet: nothing moves automatically
  (#2).
