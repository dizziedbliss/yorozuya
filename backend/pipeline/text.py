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
    lines = [line.strip() for line in text.splitlines()]
    return _BLANK_LINES.sub("\n\n", "\n".join(lines)).strip()
