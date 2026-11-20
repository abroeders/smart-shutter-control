# Repository scaffold

- Issue: #1
- Status: **approved** (2026-11-20), icon included
- Date: 2026-11-19

## 1. Purpose

Set up the repository so that the integration can be developed, tested and installed through HACS from the
first commit onward. No shutter logic is part of this issue.

## 2. Constraints

- Installs as a HACS custom repository (category *Integration*) and can later qualify for the default store.
- Minimum Home Assistant version **2026.3**: config subentries (one device per shutter, #2) and brand images
  shipped with the integration are both available there.
- No extra Python requirements. The logic (sun geometry, rules, calibration) is plain Python without Home
  Assistant imports, so it can be tested on any recent Python.

## 3. Layout

```
custom_components/smart_shutter_control/
  __init__.py          setup/unload of the config entry
  manifest.json
  const.py             domain, configuration keys, defaults
  brand/               icon.png, icon@2x.png, dark_icon.png, dark_icon@2x.png
  core/                no Home Assistant imports
    __init__.py
  config_flow.py       base controller and shutter subentries   (#2)
  coordinator.py       glue to Home Assistant                   (#2)
  cover.py, switch.py, number.py, sensor.py                     (#2)
  strings.json
  translations/en.json, translations/nl.json
frontend/              card sources (TypeScript, Lit)           (#9)
tests/                 pytest, core only
tests_ha/              Home Assistant tests
docs/                  user documentation                       (#8)
docs/design/           design documents
brand/                 icon sources (SVG)
scripts/               render_icons.py, check_mermaid.mjs
hacs.json, pyproject.toml
README.md, CHANGELOG.md, LICENSE
.github/workflows/validate.yml, tests.yml
.github/ISSUE_TEMPLATE/bug_report.yml, feature_request.yml
```

Tests add `custom_components/smart_shutter_control` to `sys.path` and import `core` directly, so the
package `__init__.py` (which imports Home Assistant) is never loaded by the core tests.

## 4. Files

### 4.1 `manifest.json`

```json
{
  "domain": "smart_shutter_control",
  "name": "Smart Shutter Control",
  "codeowners": ["@abroeders"],
  "config_flow": true,
  "dependencies": [],
  "after_dependencies": ["sun", "weather"],
  "documentation": "https://github.com/abroeders/smart-shutter-control",
  "integration_type": "hub",
  "iot_class": "calculated",
  "issue_tracker": "https://github.com/abroeders/smart-shutter-control/issues",
  "requirements": [],
  "version": "0.0.0"
}
```

- `integration_type: hub`: one entry (the base controller) with several devices (the shutters).
- `iot_class: calculated`: the integration reads other entities and controls existing cover entities; it
  talks to no device or service of its own.

### 4.2 `hacs.json`

```json
{ "name": "Smart Shutter Control", "homeassistant": "2026.3.0", "render_readme": true }
```

### 4.3 Minimal integration

For this issue the config flow has one step: a name. It creates an entry without entities. This proves that
hassfest, HACS validation and installation work before real code lands. Issue #2 replaces the flow.

## 5. CI

| Workflow | Trigger | Steps |
|---|---|---|
| `validate.yml` | push, pull request, weekly | `home-assistant/actions/hassfest`, `hacs/action` (category integration) |
| `tests.yml` | push, pull request | Python 3.13: `ruff check`, `ruff format --check`, `pytest`; Home Assistant tests with `pytest-homeassistant-custom-component`; Mermaid check of `docs/` |

Both run on `main`, `develop`, feature branches and pull requests. The card job is added with #9.

## 6. Versioning and releases

- Semantic versioning; `manifest.json` `version` is updated on release.
- `CHANGELOG.md` in *Keep a Changelog* format.
- GitHub releases with a version tag on `main`; HACS offers the releases to users. Since 2026.11.0 versions
  follow Home Assistant's scheme `YEAR.MONTH.N` (tag without `v`); before that `v0.1.0`–`v0.6.1`.

## 7. Issue templates

Bug report (version, Home Assistant version, what happened, diagnostics download) and feature request
(problem, proposal).

## 8. Brand images

- **Where it shows.** Since Home Assistant 2026.3 a custom integration can ship its own brand images in
  `custom_components/<domain>/brand/`; they take precedence over the brands repository.
- **Files:** `icon.png` (256 × 256), `icon@2x.png` (512 × 512), `dark_icon.png`, `dark_icon@2x.png`; no
  logo (Home Assistant falls back to the icon).
- **Source:** `brand/icon.svg` and `brand/dark_icon.svg`, rendered with `scripts/render_icons.py` (resvg).
- **Design:** a window with a roller shutter half way down (box, slats, bottom bar), blue glass below it, an
  up/down arrow and the sun at the top right. Flat with soft gradients, readable at 48 px, no text. The dark
  variant gets a lighter frame.

Draft:

![icon draft](assets/2026-11-19-icon-draft.png)

## 9. Out of scope

Any shutter logic; documentation content beyond the README (#8).

## 10. Acceptance

- CI green on the feature branch.
- The icon shows on *Settings → Devices & services*.
- Adding the repository as a HACS custom repository shows the integration, and the config flow creates an
  entry without errors (checked by the user).
