"""HTML job descriptions → readable plain text, keeping line breaks so section headings survive."""

import html
import re

_BLOCK_END = re.compile(r"</(p|div|li|h[1-6]|ul|ol|tr|section)>|<br\s*/?>", re.IGNORECASE)
_LIST_ITEM = re.compile(r"<li[^>]*>", re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")
_SPACES = re.compile(r"[ \t\xa0]+")
_BLANK_LINES = re.compile(r"\n\s*\n\s*\n+")


def html_to_text(raw: str | None) -> str:
    if not raw:
        return ""
    text = html.unescape(raw)
    if "<" in text and ">" in text:
        text = _LIST_ITEM.sub("\n• ", text)
        text = _BLOCK_END.sub("\n", text)
        text = _TAG.sub("", text)
        text = html.unescape(text)
    text = _SPACES.sub(" ", text)
    return _BLANK_LINES.sub(
        "\n\n", "\n".join(_tidy_bullets([line.strip() for line in text.splitlines()]))
    ).strip()


def _tidy_bullets(lines: list[str]) -> list[str]:
    """`<li>\\n<p>text</p>` leaves a bare "•" line: pull the text up onto it, and keep list items together."""
    joined: list[str] = []
    waiting = False
    for line in lines:
        if line == "•":
            waiting = True
            continue
        if waiting:
            if not line:
                continue
            line, waiting = f"• {line}", False
        joined.append(line)

    # The next non-empty line after each index, found in one backwards pass (descriptions are outside input).
    next_text = [""] * len(joined)
    upcoming = ""
    for i in range(len(joined) - 1, -1, -1):
        next_text[i] = upcoming
        if joined[i]:
            upcoming = joined[i]

    out: list[str] = []
    for i, line in enumerate(joined):
        prev = out[-1] if out else ""
        if not line and prev.startswith("• ") and next_text[i].startswith("• "):
            continue
        out.append(line)
    return out
