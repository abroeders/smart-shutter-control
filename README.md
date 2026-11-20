# Smart Shutter Control

A Home Assistant integration (HACS) that controls roller shutters.

- **Base controller:** settings for all shutters: sun and PV sources, weather, wind and the storm limit,
  holidays.
- **One device per shutter:** window direction in degrees, a profile (morning, evening, slit and night
  positions, heat protection, winter use), a maximum position for automatic control, sleep-in, and an
  on/off switch for automatic control.
- **Heat protection:** closes a shutter when the sun actually shines on its window: the sun's position
  against the window direction, with PV power as a measure of clouds.
- **Calibrated positions:** 50 % means half way down the window, whichever direction the shutter comes from.
- **Safety:** in a storm a shutter is only fully open or fully closed.
- **Manual operation is respected.**
- **Lovelace card:** a drawing of each shutter that you can drag to a position, with up, stop and down, and
  its status.

Status: in development. See the [issues](https://github.com/abroeders/smart-shutter-control/issues) for the
plan.

## Development

- Logic in `custom_components/smart_shutter_control/core/` (no Home Assistant imports): `pytest`.
- Home Assistant tests: `pytest tests_ha -o pythonpath=. -o testpaths=tests_ha -o asyncio_mode=auto` with
  `pytest-homeassistant-custom-component`.
- Code style: `ruff check .` and `ruff format .`.
- Designs: [`docs/design/`](docs/design/), architecture and UML: [`docs/architecture.md`](docs/architecture.md).
- Icons: edit `brand/*.svg`, then `python scripts/render_icons.py`.

## License

[Apache-2.0](LICENSE)
