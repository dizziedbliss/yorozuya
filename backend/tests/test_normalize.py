import pytest

from pipeline.normalize import dedupe_key, normalize_salary, parse_salary_text

RATES = {"USD": 88.0, "EUR": 95.0}


@pytest.mark.parametrize(
    ("low", "high", "currency", "period", "expected"),
    [
        (600_000, 800_000, "INR", "yearly", (6.0, 8.0)),
        (30_000, None, "INR", "monthly", (3.6, None)),
        (100_000, 120_000, "USD", "year", (88.0, 105.6)),
        (50, None, "USD", "hourly", (91.5, None)),
        (None, 4_000, "EUR", "month", (None, 45.6)),
    ],
)
def test_salaries_become_lakhs_per_annum(low, high, currency, period, expected):
    assert normalize_salary(low, high, currency, period, RATES) == expected


def test_salary_is_unknown_when_currency_has_no_rate_or_there_are_no_numbers():
    assert normalize_salary(50_000, None, "JPY", "yearly", RATES) is None
    assert normalize_salary(None, None, "INR", "yearly", RATES) is None
    assert normalize_salary(50_000, None, "INR", "fortnightly-ish", RATES) is None


def test_the_same_job_from_different_sources_gets_the_same_dedupe_key():
    a = dedupe_key(
        "Razorpay Software Pvt. Ltd.", "Software Engineer (Backend) - Intern", "Bangalore, Karnataka"
    )
    b = dedupe_key("razorpay", "Software Engineer – Backend Intern", "Bengaluru")
    assert a == b


def test_remote_variants_share_a_key_but_different_roles_or_cities_do_not():
    assert dedupe_key("Postman", "SRE Intern", "Remote - India") == dedupe_key(
        "Postman Inc", "SRE Intern", "Remote"
    )
    assert dedupe_key("Postman", "SRE Intern", "Bengaluru") != dedupe_key("Postman", "SRE Intern", "Chennai")
    assert dedupe_key("Postman", "SRE Intern", "Bengaluru") != dedupe_key(
        "Postman", "Backend Intern", "Bengaluru"
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("$25k - $35k", (25_000, 35_000, "USD", "yearly")),
        ("$80,000 - $100,000 per year", (80_000, 100_000, "USD", "yearly")),
        ("₹6-8 LPA", (600_000, 800_000, "INR", "yearly")),
        ("INR 30,000/month", (30_000, None, "INR", "monthly")),
        ("€50k", (50_000, None, "EUR", "yearly")),
        ("$45/hr", (45, None, "USD", "hourly")),
        ("$60k, needs 2 years", (60_000, None, "USD", "yearly")),
        ("Rs. 25,000 per month", (25_000, None, "INR", "monthly")),
        ("Competitive", None),
        ("", None),
    ],
)
def test_salary_text_is_parsed_into_numbers_currency_and_period(text, expected):
    assert parse_salary_text(text) == expected
