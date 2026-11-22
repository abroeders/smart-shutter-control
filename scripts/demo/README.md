# Demo Home Assistant

This is a made-up Home Assistant configuration for the screenshot demo. All names, sensor readings, and
location details are fictional; it does not use a real Home Assistant installation.

Create a virtual environment and install the requirements:

```sh
python3.14 -m venv .venv-demo
.venv-demo/bin/python -m pip install -r scripts/demo/requirements.txt
.venv-demo/bin/playwright install chromium
```

From the repository root, run the screenshot script with the Python of that environment:

```sh
.venv-demo/bin/python scripts/demo_screenshots.py            # all screenshots
.venv-demo/bin/python scripts/demo_screenshots.py dashboard  # only some: install, add_shutter, sun, storm,
                                                             # winter, shutter, table, device, assistant
SSC_DEMO_HOLD=1 .venv-demo/bin/python scripts/demo_screenshots.py none  # keep the demo running to look around
```

It writes `docs/images/ha-*.png` and `docs/images/dashboard-*.png`.
