"""The core package imports without Home Assistant."""

import sys


def test_core_imports_without_home_assistant():
    import core  # noqa: F401

    assert not any(name == "homeassistant" or name.startswith("homeassistant.") for name in sys.modules)
