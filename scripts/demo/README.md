# Demo Home Assistant

This is a made-up Home Assistant configuration for the screenshot demo. All names, sensor readings, and
location details are fictional; it does not use a real Home Assistant installation.

Create a virtual environment and install the requirements:

```sh
python3 -m venv .venv-demo
SSC_DEMO_VENV="$PWD/.venv-demo"
"$SSC_DEMO_VENV/bin/python" -m pip install -r scripts/demo/requirements.txt
"$SSC_DEMO_VENV/bin/playwright" install chromium
```

From the repository root, run the screenshot script with that environment:

```sh
SSC_DEMO_VENV="$PWD/.venv-demo" python scripts/demo_screenshots.py
```
