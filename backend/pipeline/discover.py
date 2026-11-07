"""Spot jobs whose apply link lives on a public ATS board, so the company joins the ATS list."""

import re
from urllib.parse import urlparse

_PATTERNS = (
    ("greenhouse", re.compile(r"^(?:job-)?boards(?:\.eu)?\.greenhouse\.io$"), 0),
    ("lever", re.compile(r"^jobs(?:\.eu)?\.lever\.co$"), 0),
    ("ashby", re.compile(r"^jobs\.ashbyhq\.com$"), 0),
    ("workable", re.compile(r"^apply\.workable\.com$"), 0),
    ("smartrecruiters", re.compile(r"^jobs\.smartrecruiters\.com$"), 0),
)
# Path segments that are features of the board, not company slugs.
_NOT_SLUGS = {"embed", "j", "api", "v1", "jobs", "oneclick-ui"}
_SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def ats_from_url(url: str | None) -> tuple[str, str] | None:
    if not url:
        return None
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    segments = [s for s in parsed.path.split("/") if s]
    for ats, host_pattern, position in _PATTERNS:
        if host_pattern.match(host) and len(segments) > position:
            slug = segments[position]
            if slug.lower() not in _NOT_SLUGS and _SLUG.match(slug):
                return ats, slug
    return None
