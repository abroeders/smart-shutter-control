"""MkDocs hooks (#78, #81): links to the designs open on GitHub, GitHub's theme fragments become Material's,
and the integration's icon from brand/ is the site's logo."""

import re
from pathlib import Path

from mkdocs.structure.files import File

REPO = "https://github.com/abroeders/smart-shutter-control"
ROOT = Path(__file__).resolve().parent.parent
_LINK = re.compile(r"\]\(design/([^)]*)\)")
# an image for one theme: GitHub shows it with #gh-…-mode-only, Material with #only-… (#81)
_THEME = {"#gh-light-mode-only)": "#only-light)", "#gh-dark-mode-only)": "#only-dark)"}


def _on_github(match: re.Match) -> str:
    path = match.group(1)
    return f"]({REPO}/blob/main/docs/design/{path})" if path else f"]({REPO}/tree/main/docs/design)"


def on_page_markdown(markdown: str, **_) -> str:
    markdown = _LINK.sub(_on_github, markdown)
    for github, material in _THEME.items():
        markdown = markdown.replace(github, material)
    return markdown


def on_files(files, config, **_):
    files.append(File.generated(config, "assets/icon.svg", abs_src_path=str(ROOT / "brand" / "icon.svg")))
    return files
