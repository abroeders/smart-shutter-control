"""Screenshots of the Lovelace card for the README and the docs.

Renders the built card bundle in headless Chromium with example states, as Home Assistant would publish them.

Usage: python scripts/screenshot_card.py
Needs: pip install playwright; playwright install chromium
Writes docs/images/card-*.png.
"""

from __future__ import annotations

import functools
import http.server
import json
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "images"
P = "smart_shutter_control"
BASE, LIVING, KITCHEN, BEDROOM = "base", "living", "kitchen", "bedroom"
# name, device, theme, width, language, drag to (fraction of the drawing's height) or None
SHOTS = (
    ("card-light.png", LIVING, "light", 520, "", None),
    ("card-dark.png", LIVING, "dark", 520, "", None),
    ("card-narrow.png", LIVING, "light", 330, "nl", None),
    ("card-drag.png", LIVING, "light", 520, "", 0.62),
    ("card-overview.png", BASE, "light", 900, "", None),
    ("card-overview-dark.png", BASE, "dark", 900, "", None),
)


def hass_json() -> dict:
    now = "2026-11-18T12:00:00+00:00"

    def s(state, **attributes):
        return {"state": str(state), "attributes": attributes, "last_updated": now}

    shutters = {
        LIVING: ("Living room", {
            "shutter": ("cover", s("open", current_position=62)),
            "reason": ("sensor", s("sun", target_position=30, max_position=80, language=None)),
            "next_action": ("sensor", s("2026-11-18T15:55:00+00:00", phase="dusk", position=35, following=[
                {"at": "2026-11-18T16:10:00+00:00", "phase": "night", "position": 0},
                {"at": "2026-11-19T07:00:00+00:00", "phase": "slit", "position": "slit"}])),
            "stand": ("sensor", s("partly_open")),
            "phase": ("sensor", s("day")),
            "automatic": ("switch", s("on")),
            "sleep_in": ("switch", s("off")),
            "manual_pause": ("binary_sensor", s("off")),
            "resume": ("button", s("unknown")),
        }),
        KITCHEN: ("Kitchen", {
            "shutter": ("cover", s("closed", current_position=0)),
            "reason": ("sensor", s("sleep_in", target_position=0, max_position=100)),
            "automatic": ("switch", s("on")),
            "sleep_in": ("switch", s("on")),
        }),
        BEDROOM: ("Bedroom", {
            "shutter": ("cover", s("open", current_position=90)),
            "reason": ("sensor", s("manual", target_position=None, max_position=100)),
            "manual_pause": ("binary_sensor", s("on", until="2026-11-18T15:55:00+00:00")),
            "automatic": ("switch", s("on")),
        }),
        BASE: ("House", {
            "storm": ("binary_sensor", s("off")),
            "frost": ("binary_sensor", s("off")),
            "sleep_in_all": ("switch", s("off")),
        }),
    }  # fmt: skip
    states, entities, devices = {}, {}, {}
    for device, (name, ents) in shutters.items():
        devices[device] = {"id": device, "name": name, "via_device_id": None if device == BASE else BASE}
        for key, (domain, state) in ents.items():
            eid = f"{domain}.{device}_{key}"
            states[eid] = {"entity_id": eid, **state}
            entities[eid] = {"entity_id": eid, "device_id": device, "platform": P, "translation_key": key}
    return {
        "states": states,
        "entities": entities,
        "devices": devices,
        "locale": {"language": "en"},
        "config": {"time_zone": "Europe/Amsterdam"},
    }


def main() -> None:
    from playwright.sync_api import sync_playwright

    data = ROOT / "scripts" / "screenshots" / "hass.json"
    data.write_text(json.dumps(hass_json()))
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for name, device, theme, width, lang, drag in SHOTS:
                page = browser.new_page(
                    viewport={"width": width + 32, "height": 900},
                    device_scale_factor=2,
                    timezone_id="Europe/Amsterdam",
                )
                page.emulate_media(reduced_motion="reduce")
                page.goto(
                    f"http://127.0.0.1:{port}/scripts/screenshots/harness.html"
                    f"?theme={theme}&width={width}&device={device}&lang={lang}"
                )
                page.wait_for_function("window.__ready === true")
                if drag is not None:
                    box = page.locator("ssc-drawing svg").bounding_box()
                    x = box["x"] + box["width"] * 0.6
                    page.mouse.move(x, box["y"] + box["height"] * 0.3)
                    page.mouse.down()
                    page.mouse.move(x, box["y"] + box["height"] * drag, steps=5)
                    page.wait_for_timeout(100)
                page.locator("#host").screenshot(path=str(OUT / name))
                print(OUT / name)
            browser.close()
    finally:
        server.shutdown()
        data.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
