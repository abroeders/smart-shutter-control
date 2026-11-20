"""Render the brand PNGs from the SVG sources in brand/.

Usage: python scripts/render_icons.py   (needs: pip install resvg-py)
"""

from pathlib import Path

import resvg_py

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "brand"
TARGET = ROOT / "custom_components" / "smart_shutter_control" / "brand"

for name in ("icon", "dark_icon"):
    svg = (SOURCE / f"{name}.svg").read_text()
    for size, suffix in ((256, ""), (512, "@2x")):
        png = bytes(resvg_py.svg_to_bytes(svg_string=svg, width=size, height=size))
        (TARGET / f"{name}{suffix}.png").write_bytes(png)
        print(f"{name}{suffix}.png")
