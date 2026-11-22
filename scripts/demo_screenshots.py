"""Screenshots of Home Assistant for the docs (#81): setup, settings, calibration, device page, dashboard.

Starts a made-up demo Home Assistant (scripts/demo/) in a temporary directory, sets up the integration through
its config flows, saves a dashboard and takes each screenshot in headless Chromium. Nothing comes from a real
installation. The longitude is chosen so it is about 13:00 solar time now: the sun stands high in the south.

Usage: <venv>/bin/python scripts/demo_screenshots.py [name ...]   (only the named shots)
Needs: a venv with scripts/demo/requirements.txt, and `playwright install chromium` in it.
SSC_DEMO_HOLD=1 keeps the demo running after the shots, for a look in the browser at the URL below.
Writes docs/images/ha-*.png and docs/images/dashboard-*.png.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "images"
DEMO = ROOT / "scripts" / "demo"
PORT = 18123
URL = f"http://127.0.0.1:{PORT}"
CLIENT = f"{URL}/"
PASSWORD = "demo-demo"  # a throw-away demo on 127.0.0.1
DOMAIN = "smart_shutter_control"
SHUTTERS = (  # cover, window direction (south, east, west); the first has a travel time
    ("cover.living_room", 180, 30),
    ("cover.kitchen", 90, None),
    ("cover.bedroom", 270, None),
)


def solar_longitude(hour: float = 13.0) -> float:
    """The longitude where it is `hour` solar time now (UTC + longitude / 15)."""
    now = datetime.now(UTC)
    utc = now.hour + now.minute / 60
    return round(((hour - utc) * 15 + 180) % 360 - 180, 2)


# --- the demo Home Assistant ---------------------------------------------------------------------------


def prepare(config: Path) -> None:
    shutil.copy(DEMO / "configuration.yaml", config / "configuration.yaml")
    text = (config / "configuration.yaml").read_text()
    text = text.replace("longitude: 0", f"longitude: {solar_longitude()}")
    text += f"\nhttp:\n  server_port: {PORT}\n"
    # 'Home Assistant initialized' tells that it has started
    text += "\nlogger:\n  default: warning\n  logs:\n    homeassistant.bootstrap: info\n"
    (config / "configuration.yaml").write_text(text)
    (config / "custom_components").mkdir()
    (config / "custom_components" / DOMAIN).symlink_to(ROOT / "custom_components" / DOMAIN)


def request(path: str, data: dict | None = None, token: str | None = None, form: bool = False) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    body = None
    if data is not None:
        if form:
            body = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in data.items()).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
    req = urllib.request.Request(URL + path, data=body, headers=headers, method="POST" if body else "GET")
    with urllib.request.urlopen(req, timeout=120) as response:
        raw = response.read()
    return json.loads(raw) if raw else {}


def wait_for_start(process: subprocess.Popen, log: Path) -> None:
    """Until Home Assistant has started (the first start installs the frontend's requirements)."""
    for _ in range(600):
        if process.poll() is not None:
            sys.exit(f"Home Assistant stopped while starting; see {log}")
        if "Home Assistant initialized" in log.read_text():
            return
        time.sleep(1)
    sys.exit("Home Assistant did not start")


def onboard() -> dict:
    """Onboarding through the REST API; the tokens for the API and for the browser."""
    user = {
        "client_id": CLIENT,
        "name": "Demo",
        "username": "demo",
        "password": "demo-demo",
        "language": "en",
    }
    code = request("/api/onboarding/users", user)["auth_code"]
    tokens = request(
        "/auth/token", {"grant_type": "authorization_code", "code": code, "client_id": CLIENT}, form=True
    )
    token = tokens["access_token"]
    request("/api/onboarding/core_config", {}, token)
    request("/api/onboarding/analytics", {}, token)
    request(
        "/api/onboarding/integration", {"client_id": CLIENT, "redirect_uri": f"{URL}/?auth_callback=1"}, token
    )
    return tokens


def flow(path: str, start: dict, steps: list[dict], token: str) -> dict:
    result = request(path, start, token)
    for data in steps:
        result = request(f"{path}/{result['flow_id']}", data, token)
    return result


def set_up(token: str) -> str:
    """The base controller and the shutters; the base controller's entry id."""
    entry = flow(
        "/api/config/config_entries/flow",
        {"handler": DOMAIN},
        [
            {"name": "Smart Shutter Control"},
            {
                "outdoor_temperature": "sensor.outdoor_temperature",
                "sun_source": "pv",
                "wind_speed": "sensor.wind_speed",
                "wind_gust": "sensor.wind_gust",
            },
            {"pv_power": ["sensor.pv_power"], "pv_peak": 4.0},
        ],
        token,
    )["result"]["entry_id"]
    for cover, azimuth, travel in SHUTTERS:
        data = {"cover": cover, "azimuth": azimuth}
        if travel:
            data["travel_time"] = travel
        if cover == "cover.living_room":  # a room sensor and the room's geometry
            data |= {
                "room_temperature": "sensor.living_room_temperature",
                "window_sill": 80,
                "window_height": 150,
                "sun_depth": 1.5,
            }
        flow("/api/config/config_entries/subentries/flow", {"handler": [entry, "shutter"]}, [data], token)
    return entry


def template(text: str, token: str) -> str:
    req = urllib.request.Request(
        URL + "/api/template",
        data=json.dumps({"template": text}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode().strip()


def device(name: str, token: str) -> str:
    """The device id of one of the integration's devices: 'base' or a cover's object id."""
    return template(
        f"{{{{ integration_entities('{DOMAIN}') | map('device_id') | unique"
        f" | select('is_device_attr', 'name', '{name}') | first }}}}",
        token,
    )


DIALOG = "ha-dialog, ha-md-dialog, ha-adaptive-dialog"
SURFACE = ", ".join(
    f"{d} :is(.mdc-dialog__surface, [part=dialog], dialog):visible" for d in DIALOG.split(", ")
)


# only the dialog: the page behind it and the dimmed backdrop hidden, so the rounded corners are transparent
ALONE = """() => {
  const root = document.querySelector("home-assistant").shadowRoot;
  root.querySelector("home-assistant-main").style.visibility = "hidden";
  const style = document.createElement("style");
  style.textContent = `html, body { background: transparent !important; }
    * { --mdc-dialog-scrim-color: transparent; --dialog-backdrop-filter: none; }`;
  document.head.append(style);
}"""


class Browser:
    """A logged-in page in headless Chromium, and the helpers to take the screenshots."""

    def __init__(self, playwright, tokens: dict, theme: str = "light") -> None:
        self.browser = playwright.chromium.launch()
        context = self.browser.new_context(
            viewport={"width": 1280, "height": 900}, device_scale_factor=2, color_scheme=theme
        )
        stored = {**tokens, "hassUrl": URL, "clientId": CLIENT, "expires": int(time.time() * 1000) + 1800_000}
        context.add_init_script(f"localStorage.setItem('hassTokens', {json.dumps(json.dumps(stored))});")
        self.page = context.new_page()

    def open(self, path: str) -> None:
        self.page.goto(URL + path)
        self.page.wait_for_load_state("networkidle")
        confirm = self.page.get_by_role("button", name="Confirm")  # the new HTTP port, once
        if confirm.count():
            confirm.first.click()
        self.page.wait_for_timeout(1500)

    def wait(self) -> None:
        self.page.wait_for_timeout(1200)

    def choose(self, item: str) -> None:
        """A menu item in the open dialog."""
        self.wait()
        self.page.locator(DIALOG).last.get_by_text(item, exact=True).click()

    def dialog(self, name: str, tall: bool = False, top: int | None = None) -> None:
        """The open dialog's surface; `tall`: a long form, in a taller window so it fits without scrolling;
        `top`: only its upper part, that many pixels high (a list with much empty space below)."""
        self.page.set_viewport_size({"width": 1280, "height": 3200 if tall else 900})
        self.wait()
        surface = self.page.locator(SURFACE).last  # the visible one: a closing dialog may still be there
        self.page.evaluate(ALONE)
        try:
            if top:
                box = surface.bounding_box()
                clip = {**box, "height": min(top, box["height"])}
                self.page.screenshot(path=OUT / name, clip=clip, omit_background=True)
            else:
                surface.screenshot(path=OUT / name, omit_background=True)
        except Exception:
            self.page.screenshot(path=OUT / f"failed-{name}")
            raise
        self.page.set_viewport_size({"width": 1280, "height": 900})

    def whole(self, name: str) -> None:
        self.page.wait_for_timeout(1500)
        self.page.screenshot(path=OUT / name)

    def close(self) -> None:
        self.browser.close()


async def _save_dashboard(token: str, devices: dict[str, str]) -> None:
    import aiohttp  # comes with Home Assistant

    config = {
        "title": "Home",
        "views": [
            {
                "title": "Shutters",
                "path": "shutters",
                "type": "sections",
                "max_columns": 3,
                "sections": [
                    {
                        "type": "grid",
                        "cards": [{"type": "custom:smart-shutter-card", "device_id": devices["base"]}],
                    },
                    {
                        "type": "grid",
                        "cards": [{"type": "custom:smart-shutter-card", "device_id": devices["living"]}],
                    },
                    {
                        "type": "grid",
                        "cards": [{"type": "custom:smart-shutter-card", "device_id": devices["kitchen"]}],
                    },
                ],
            }
        ],
    }
    async with aiohttp.ClientSession() as session, session.ws_connect(f"{URL}/api/websocket") as ws:
        await ws.receive_json()
        await ws.send_json({"type": "auth", "access_token": token})
        await ws.receive_json()
        dashboard = {"url_path": "dashboard-shutters", "title": "Shutters", "icon": "mdi:window-shutter"}
        messages = (
            {"id": 1, "type": "lovelace/dashboards/create", "mode": "storage", **dashboard},
            {"id": 2, "type": "lovelace/config/save", "url_path": dashboard["url_path"], "config": config},
        )
        for message in messages:
            await ws.send_json(message)
            result = await ws.receive_json()
            if not result.get("success"):
                sys.exit(f"Saving the dashboard failed: {result}")


def shots(browser: Browser, devices: dict[str, str]) -> dict:
    """Each screenshot: its file name and how to take it."""
    page = browser.page

    def install() -> None:
        browser.open("/config/integrations/dashboard")
        page.get_by_role("button", name="Add integration").click()
        page.wait_for_timeout(1500)
        page.keyboard.type("Smart Shutter")
        browser.dialog("ha-install-search.png", top=170)
        page.get_by_text("Smart Shutter Control").last.click()
        page.wait_for_timeout(2500)  # the search dialog closes first
        page.keyboard.press("End")  # the name is selected
        browser.dialog("ha-install-name.png")
        page.get_by_role("button", name="Submit").click()
        browser.dialog("ha-install-sources.png", tall=True)

    def add_shutter() -> None:
        browser.open(f"/config/integrations/integration/{DOMAIN}")
        page.get_by_role("button", name="Add shutter").first.click()
        browser.dialog("ha-install-shutter.png", tall=True)

    def options(item: str, name: str) -> None:
        browser.open(f"/config/integrations/integration/{DOMAIN}")
        page.get_by_role("button", name="Configure").first.click()
        browser.choose(item)
        browser.dialog(name, tall=True)

    def living_room(item: str) -> None:
        """The reconfigure menu of the shutter 'Living room' (the third, alphabetically)."""
        browser.open(f"/config/integrations/integration/{DOMAIN}")
        page.get_by_role("button", name="Change shutter").nth(2).click()
        browser.choose(item)
        browser.wait()

    def shutter_settings() -> None:
        living_room("Settings")
        browser.dialog("ha-config-shutter.png", tall=True)

    def assistant() -> None:
        living_room("Calibrate")
        browser.dialog("ha-cal-menu.png")
        browser.choose("Assistant")
        browser.dialog("ha-cal-start.png")
        page.locator(DIALOG).last.locator("input").first.fill("150")
        page.get_by_role("button", name="Submit").click()
        page.get_by_text("The bottom bar has lifted").wait_for(timeout=120_000)
        browser.dialog("ha-cal-lift.png")
        page.locator(DIALOG).last.locator("ha-switch").click()  # it has lifted: the measuring starts
        page.get_by_role("button", name="Submit").click()
        page.get_by_text("How far is the window open").wait_for(timeout=120_000)
        browser.dialog("ha-cal-measure.png")

    def table() -> None:
        living_room("Calibrate")
        browser.choose("Edit table")
        browser.dialog("ha-cal-table.png", tall=True)

    def device_page() -> None:
        browser.open(f"/config/devices/device/{devices['living']}")
        browser.whole("ha-device.png")

    return {
        "install": install,
        "add_shutter": add_shutter,
        "sun": lambda: options("Sun", "ha-config-sun.png"),
        "storm": lambda: options("Storm and frost", "ha-config-storm.png"),
        "winter": lambda: options("Winter", "ha-config-winter.png"),
        "shutter": shutter_settings,
        "table": table,
        "device": device_page,
        "assistant": assistant,  # last: it leaves the shutter calibrating
    }


def screenshots(tokens: dict, wanted: set[str]) -> None:
    import asyncio

    from playwright.sync_api import sync_playwright  # only in the demo's venv

    token = tokens["access_token"]
    devices = {
        "base": device("Smart Shutter Control", token),
        "living": device("Living room", token),
        "kitchen": device("Kitchen", token),
    }
    asyncio.run(_save_dashboard(token, devices))
    with sync_playwright() as playwright:
        if not wanted or "dashboard" in wanted:  # first: before the calibration moves a shutter
            for theme in ("light", "dark"):
                browser = Browser(playwright, tokens, theme)
                browser.open("/dashboard-shutters/shutters")
                browser.page.locator("smart-shutter-card").last.wait_for(timeout=60_000)
                browser.page.wait_for_timeout(3000)  # the drawings
                browser.whole(f"dashboard-{theme}.png")
                browser.close()
        browser = Browser(playwright, tokens)
        for name, take in shots(browser, devices).items():
            if not wanted or name in wanted:
                print("shot", name)
                take()
        browser.close()


def main() -> None:
    hass = Path(sys.executable).with_name("hass")
    if not hass.exists():
        sys.exit("Run this with the Python of a venv with scripts/demo/requirements.txt")
    wanted = set(sys.argv[1:])
    with tempfile.TemporaryDirectory(prefix="ssc-demo-") as tmp:
        config = Path(tmp)
        prepare(config)
        log = (config / "hass.log").open("w")
        process = subprocess.Popen([hass, "-c", str(config)], stdout=log, stderr=log)
        try:
            wait_for_start(process, config / "hass.log")
            tokens = onboard()
            set_up(tokens["access_token"])
            time.sleep(5)  # the controllers' first decisions
            screenshots(tokens, wanted)
            if os.environ.get("SSC_DEMO_HOLD"):
                input(f"Demo at {URL} (demo / {PASSWORD}); Enter stops it ")
        finally:
            process.terminate()
            process.wait(timeout=60)
            if os.environ.get("SSC_DEMO_KEEP_LOG"):
                shutil.copy(config / "hass.log", ROOT / "demo-hass.log")


if __name__ == "__main__":
    main()
