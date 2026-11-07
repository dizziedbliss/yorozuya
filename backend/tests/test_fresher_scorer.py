from ranking.fresher import score_fresher


def test_devops_intern_in_bengaluru_is_kept_with_role_and_level_chips():
    result = score_fresher(
        title="DevOps Intern",
        description="Help us run our CI pipelines.",
        location="Bengaluru, Karnataka, India",
    )

    assert result.dropped is None
    assert result.score > 0
    assert "devops" in result.matched
    assert "intern" in result.matched


def test_senior_or_lead_titles_are_dropped_even_when_the_role_matches():
    for title in [
        "Senior DevOps Engineer",
        "Staff SRE",
        "Lead Backend Engineer",
        "Platform Engineering Manager",
    ]:
        result = score_fresher(title=title, description="", location="Remote")
        assert result.dropped == "too senior", title


def test_titles_outside_my_roles_are_dropped_even_for_interns():
    result = score_fresher(title="Marketing Intern", description="", location="Remote")
    assert result.dropped == "not my role"


def test_jds_asking_for_three_or_more_years_are_dropped():
    for jd in [
        "You have 3+ years of experience running Kubernetes.",
        "Requirements: 3-5 years experience in backend development",
        "Minimum 4 years of professional experience",
        "Experience: 5 yrs in cloud infrastructure",
    ]:
        result = score_fresher(title="Backend Engineer", description=jd, location="Remote")
        assert result.dropped == "wants 3+ years", jd


def test_jds_asking_for_up_to_two_years_are_kept():
    for jd in [
        "0-2 years of experience",
        "1+ years experience with Python",
        "We have 10 years of history and 300 customers.",
    ]:
        result = score_fresher(title="Backend Engineer", description=jd, location="Remote")
        assert result.dropped is None, jd


def test_location_keeps_remote_anywhere_bengaluru_and_chennai():
    for location in [
        "Remote",
        "Remote - US",
        "Anywhere in the world",
        "India (Remote)",
        "Bangalore",
        "Bengaluru, Karnataka, India",
        "Hybrid - Chennai",
        "Pune or Bengaluru",
        "India",
        "",
        None,
    ]:
        result = score_fresher(title="SRE Intern", description="", location=location)
        assert result.dropped is None, location


def test_location_drops_other_cities():
    for location in ["Mumbai, India", "New York, NY", "London, UK", "Hyderabad"]:
        result = score_fresher(title="SRE Intern", description="", location=location)
        assert result.dropped == "wrong city", location


def test_techs_from_the_jd_become_chips_without_false_positives():
    jd = (
        "We go beyond the usual. Our team ships on GitHub every day.\n"
        "Tech: Python, Go, Docker, k8s, Terraform and GitHub Actions. CI/CD with PostgreSQL."
    )
    result = score_fresher(title="Platform Intern", description=jd, location="Remote")

    assert set(result.techs) == {
        "python",
        "go",
        "docker",
        "kubernetes",
        "terraform",
        "github actions",
        "ci/cd",
        "postgresql",
    }


def test_go_counts_when_written_as_golang_or_in_a_list():
    for jd in ["Golang microservices", "Languages: Go/Python", "(Go) services", "Java, Go and Rust"]:
        result = score_fresher(title="Backend Intern", description=jd, location="Remote")
        assert "go" in result.techs, jd


def test_techs_under_a_requirements_heading_weigh_more_than_in_the_intro():
    intro = score_fresher(
        title="Backend Intern",
        description="We use Docker everywhere.\nRequirements:\nCuriosity.",
        location="Remote",
    )
    required = score_fresher(
        title="Backend Intern",
        description="About us: we ship fast.\nRequirements:\nDocker.",
        location="Remote",
    )
    assert required.score > intro.score > score_fresher("Backend Intern", "", "Remote").score


def test_fresher_signals_in_the_jd_add_score_and_a_chip():
    base = score_fresher("Software Engineer", "Build things.", "Bengaluru").score
    for jd, chip in [
        ("Open to 2027 batch graduates", "2027 batch"),
        ("0-1 years of experience", "0-2 yrs"),
        ("Freshers are welcome to apply", "freshers welcome"),
        ("Currently pursuing a B.E. in CSE", "students ok"),
    ]:
        result = score_fresher("Software Engineer", jd, "Bengaluru")
        assert chip in result.matched, jd
        assert result.score > base, jd
