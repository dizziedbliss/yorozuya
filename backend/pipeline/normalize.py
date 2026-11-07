"""Turns messy source data into comparable values: salary in ₹ LPA, and a dedupe key."""

import re

INR_PER_LAKH = 100_000

# How many of each period make a year. A full-time year: 52 weeks × 40 h, 260 working days.
PERIODS_PER_YEAR: dict[str, int] = {
    "year": 1,
    "yearly": 1,
    "annual": 1,
    "annually": 1,
    "month": 12,
    "monthly": 12,
    "week": 52,
    "weekly": 52,
    "day": 260,
    "daily": 260,
    "hour": 2080,
    "hourly": 2080,
}


def normalize_salary(
    low: float | None,
    high: float | None,
    currency: str | None,
    period: str | None,
    rates_to_inr: dict[str, float],
) -> tuple[float | None, float | None] | None:
    """Returns (min, max) in lakhs per annum, or None when the pay can't be worked out."""
    if low is None and high is None:
        return None

    code = (currency or "INR").upper()
    rate = 1.0 if code == "INR" else rates_to_inr.get(code)
    per_year = PERIODS_PER_YEAR.get((period or "yearly").lower())
    if rate is None or per_year is None:
        return None

    def to_lpa(amount: float | None) -> float | None:
        if amount is None:
            return None
        return round(amount * per_year * rate / INR_PER_LAKH, 1)

    return to_lpa(low), to_lpa(high)


# Trailing words that don't tell two companies apart ("Razorpay Software Pvt. Ltd." == "Razorpay").
COMPANY_SUFFIXES = {
    "pvt",
    "private",
    "ltd",
    "limited",
    "inc",
    "llc",
    "llp",
    "corp",
    "corporation",
    "co",
    "gmbh",
    "software",
    "technologies",
    "technology",
    "tech",
    "labs",
    "india",
}
CITY_ALIASES = {"bangalore": "bengaluru", "madras": "chennai", "gurgaon": "gurugram"}


def _words(text: str) -> list[str]:
    return re.sub(r"[^a-z0-9+#]+", " ", text.lower()).split()


def _company(name: str) -> str:
    words = _words(name)
    while len(words) > 1 and words[-1] in COMPANY_SUFFIXES:
        words.pop()
    return " ".join(words)


def _city(location: str | None) -> str:
    loc = (location or "").lower()
    if "remote" in loc:
        return "remote"
    first = _words(loc.split(",")[0])
    city = " ".join(first)
    return CITY_ALIASES.get(city, city)


def dedupe_key(company: str, title: str, location: str | None) -> str:
    """Same company + same title words + same city = the same job, whichever board it came from."""
    return f"{_company(company)}|{' '.join(_words(title))}|{_city(location)}"
