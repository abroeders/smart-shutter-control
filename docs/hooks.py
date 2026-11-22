"""MkDocs hook (#78): the designs stay out of the site, so links to them open on GitHub."""

import re

REPO = "https://github.com/abroeders/smart-shutter-control"
_LINK = re.compile(r"\]\(design/([^)]*)\)")


def _on_github(match: re.Match) -> str:
    path = match.group(1)
    return f"]({REPO}/blob/main/docs/design/{path})" if path else f"]({REPO}/tree/main/docs/design)"


def on_page_markdown(markdown: str, **_) -> str:
    return _LINK.sub(_on_github, markdown)
