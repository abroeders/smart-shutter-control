# Diagnostics for the integration

- Issue: #91
- Status: **approved** (2026-11-24)
- Date: 2026-11-24

## 1. Purpose

When something goes wrong, a user now has to copy states and attributes of many entities by hand to explain what
the integration did. Home Assistant offers a standard way for this: *Settings → Devices & services → Smart
Shutter Control → ⋮ → Download diagnostics* gives one JSON file that the user can attach to an issue. Reviewers of
the Marketplace and users often ask for it.

## 2. What the user sees

- The menu of the integration's entry gets *Download diagnostics*. The file covers the base controller and every
  shutter (one config entry with subentries), so there is no separate download per device.
- The file holds no location: coordinates and the location name are replaced by `**REDACTED**`. Entity IDs of
  persons and device trackers are redacted too. Names of shutters and the other entity IDs stay, because they are
  needed to understand the file; the documentation says so, so the user can check the file before sharing it.

## 3. Content

```json
{
  "integration": {"version": "2026.11.25", "home_assistant": "2026.11.0", "unit_system": "metric",
                   "time_zone": "Europe/Amsterdam"},
  "entry": {"data": {...}, "options": {...}},            // redacted, see 4
  "base": {
    "paused": false,
    "sun": {"elevation": 12.3, "azimuth": 140.2, "source": "pv_peak", "factor": 0.97, "sunny": true},
    "weather": {"outdoor": 4.5, "wind": 12.0, "storm": false, "frost": false, "forecast_max": 6.0,
                "winter": true, "hot_day": false},
    "clear_sky_reference": {"cells": 18, "days": 30}       // a summary, not the learned data
  },
  "shutters": [
    {
      "title": "Living room", "subentry_id": "…", "cover": "cover.living_room",
      "data": {...},                                       // the subentry's settings, redacted
      "state": {"position": 40, "module_position": 52, "phase": "day", "reason": "glare",
                "target_position": 20, "manual_pause": false, "stuck": false, "calibrated": true},
      "decision": [...],                                   // the same list as the reason sensor's attribute
      "next_action": {...},                                // the same as the next action sensor
      "position_memory": {"sent": [52, 40, "down"], "direction": "down", "anchor": 52}
    }
  ]
}
```

The numbers are examples. Every value comes from what the integration already computes for its entities; the
diagnostics compute nothing new.

## 4. Redaction

- `TO_REDACT`: `latitude`, `longitude`, `elevation`, `location_name`, `home_zone` and any other key that holds a
  place, applied with `homeassistant.components.diagnostics.async_redact_data` to the entry, the options and
  every subentry's data.
- Every string value that starts with `person.` or `device_tracker.` is replaced by `**REDACTED**`, wherever it
  appears. The settings hold no such entities today; this is a safety net for later settings (such as presence).
- Holiday calendars and extra holidays stay: they hold dates and names of public holidays, not personal data.

## 5. Design

- `diagnostics.py` (HA layer): `async_get_config_entry_diagnostics(hass, entry)` builds the dict from
  `entry.runtime_data` and redacts it. It only collects; it does not compute.
- `BaseCoordinator.diagnostics()` and `ShutterController.diagnostics()` return plain dicts with the runtime part
  of 3, from the values the entities already show (Information Expert: each object describes its own state).
  The entities' attribute code is reused where it builds the same values, instead of copied.
- No changes to `core/`; nothing in diagnostics blocks the event loop (only memory reads).
- Architecture: the class diagram gets the `diagnostics` module and the two methods.

## 6. Tests

`tests_ha/test_diagnostics.py`:
- With a base controller and two shutters, the file has the sections of 3 for both shutters, with the values of
  the entities (phase, reason, decision).
- Latitude, longitude and the location name are redacted; a `person.` value placed in a subentry's data by the
  test is redacted; the cover entity ID is not.
- Without any shutter the file has an empty `shutters` list.
- The result is JSON-serialisable (`json.dumps` works).

## 7. Documentation

- `docs/faq.md` (troubleshooting): how to download the diagnostics, what is in them, what is redacted and that the
  user should check the file before attaching it to an issue.
- The issue template's bug report asks for the diagnostics file.
- Changelog.

## 8. Work split

Claude writes this design and checks the result. Copilot builds sections 5–7 (about 200 lines, following the
existing entity and test patterns), with one test run, without committing. Claude runs `ssc-check`, reads the
diff, checks the redaction by hand and commits.

## 9. Out of scope

- Diagnostics per device (`async_get_device_diagnostics`).
- The learned clear-sky reference in full (only a summary, see 3).
- Logs; the user can turn on debug logging separately.
