"""Scores a job for fresher mode. Pure function: no I/O, every weight in fresher_weights."""

import re
from dataclasses import dataclass, field

from ranking import fresher_weights as w


@dataclass
class FresherScore:
    score: int
    matched: list[str] = field(default_factory=list)
    techs: list[str] = field(default_factory=list)
    dropped: str | None = None
    # (label, points) for every part of the score; the parts add up to `score`.
    breakdown: list[tuple[str, int]] = field(default_factory=list)


def _hits(table: dict[str, tuple[str, int]], text: str) -> list[tuple[str, int]]:
    return [(label, weight) for label, (pattern, weight) in table.items() if re.search(pattern, text)]


def _min_years_asked(text: str) -> int | None:
    found = [int(m.group(1)) for pattern in w.EXPERIENCE_PATTERNS for m in re.finditer(pattern, text)]
    return max(found) if found else None


def _location_ok(location: str | None) -> bool:
    loc = (location or "").strip().lower()
    if not loc:
        return True
    return bool(re.search(w.LOCATION_OK, loc) or re.search(w.LOCATION_COUNTRY_ONLY_OK, loc))


def _techs(description: str) -> list[tuple[str, int]]:
    heading = re.search(w.REQUIREMENTS_HEADING, description)
    required_part = description[heading.end() :] if heading else ""
    found = []
    for label, (pattern, weight) in w.TECHS.items():
        if re.search(pattern, required_part, re.IGNORECASE):
            found.append((label, weight * w.REQUIREMENTS_MULTIPLIER))
        elif re.search(pattern, description, re.IGNORECASE):
            found.append((label, weight))
    return found


def title_is_my_role(title: str) -> bool:
    """Cheap pre-filter for sources where fetching a description costs a request."""
    t = title.lower()
    return (
        not re.search(w.TOO_SENIOR_TITLE, t)
        and not re.search(w.NOT_MY_ROLE_TITLE, t)
        and bool(_hits(w.ROLE_TITLE, t))
    )


def score_fresher(title: str, description: str, location: str | None) -> FresherScore:
    t = title.lower()
    role_hits = _hits(w.ROLE_TITLE, t)
    if not role_hits or re.search(w.NOT_MY_ROLE_TITLE, t):
        return FresherScore(score=0, dropped="not my role")

    if re.search(w.TOO_SENIOR_TITLE, t):
        return FresherScore(score=0, dropped="too senior")

    if not _location_ok(location):
        return FresherScore(score=0, dropped="wrong city")

    d = description.lower()
    years = _min_years_asked(d)
    if years is not None and years >= w.DROP_AT_YEARS:
        return FresherScore(score=0, dropped="wants 3+ years")

    matched: list[str] = []
    breakdown: list[tuple[str, int]] = []
    level_labels = set(w.LEVEL_TITLE)

    for label, weight in role_hits + _hits(w.LEVEL_TITLE, t):
        matched.append(label)
        kind = "level" if label in level_labels else "role"
        breakdown.append((f"{kind}: {label}", weight * w.TITLE_MULTIPLIER))

    for label, weight in _hits(w.LEVEL_DESCRIPTION, d):
        if label not in matched:
            matched.append(label)
            breakdown.append((f"jd: {label}", weight))

    techs = _techs(description)
    tech_total = sum(weight for _, weight in techs)
    if tech_total > w.TECH_SCORE_CAP:
        breakdown.append(("your stack (capped)", w.TECH_SCORE_CAP))
    else:
        breakdown += [(f"tech: {label}", weight) for label, weight in techs]

    loc = (location or "").strip().lower()
    for pattern, bonus in w.LOCATION_BONUS:
        if found := re.search(pattern, loc):
            breakdown.append((f"location: {found.group(0)}", bonus))
            break

    score = sum(points for _, points in breakdown)
    return FresherScore(
        score=score, matched=matched, techs=[label for label, _ in techs], breakdown=breakdown
    )
