"""Checks on the integration's files: no blocking calls on the event loop (#89), translations agree (#90)."""

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "custom_components" / "smart_shutter_control"

# calls that can block Home Assistant's event loop (disk, sleep, synchronous network)
BLOCKING = re.compile(
    r"\bZoneInfo\(|\btime\.sleep\(|(?<![\w.])open\(|\.read_text\(|\.write_text\(|\.read_bytes\(|"
    r"\.exists\(\)|\bos\.listdir\(|\bos\.scandir\(|\brequests\.|\burllib\.request\b"
)
# functions that only run in an executor (hass.async_add_executor_job), so they may block
EXECUTOR_ONLY = {
    ("coordinator.py", "entity_names"),  # read with async_add_executor_job in BaseCoordinator.async_start
}


def _functions(tree: ast.AST) -> list[tuple[int, int, str]]:
    return [
        (node.lineno, node.end_lineno or node.lineno, node.name)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _blocking_calls() -> list[str]:
    found = []
    for path in sorted(ROOT.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        functions = _functions(ast.parse(source))
        for number, line in enumerate(source.splitlines(), 1):
            code = line.split("#", 1)[0]
            if not BLOCKING.search(code):
                continue
            inner = [f for f in functions if f[0] <= number <= f[1]]
            name = min(inner, key=lambda f: f[1] - f[0])[2] if inner else ""
            if (path.name, name) not in EXECUTOR_ONLY:
                found.append(f"{path.relative_to(ROOT)}:{number} in {name or 'module'}: {line.strip()}")
    return found


def test_no_blocking_calls_on_the_event_loop():
    assert _blocking_calls() == []


def _keys(data, prefix=""):
    if not isinstance(data, dict):
        return {prefix}
    return set().union(*(_keys(v, f"{prefix}/{k}") for k, v in data.items())) if data else {prefix}


def _load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_strings_json_is_the_english_translation():
    assert _load("strings.json") == _load("translations/en.json")


def test_dutch_translation_has_the_same_keys():
    english, dutch = _keys(_load("translations/en.json")), _keys(_load("translations/nl.json"))
    assert sorted(english - dutch) == [], "missing in nl.json"
    assert sorted(dutch - english) == [], "not in en.json"
