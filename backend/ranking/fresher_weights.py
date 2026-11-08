"""Every weight the fresher scorer uses. Tune here, nowhere else.

Keys are the chip labels shown in the UI; values are (regex, weight). Regexes are matched
case-insensitively against lowercased text unless noted.
"""

# Title must hit at least one of these, or the job is dropped as "not my role".
ROLE_TITLE: dict[str, tuple[str, int]] = {
    "sre": (r"\bsre\b|site reliability", 25),
    "devops": (r"\bdevops\b|\bdev ops\b", 25),
    "devsecops": (r"\bdevsecops\b", 22),
    "platform": (r"\bplatform\b", 18),
    "cloud": (r"\bcloud\b", 15),
    "infra": (r"\binfra(structure)?\b", 15),
    "mlops": (r"\bmlops\b", 12),
    "backend": (r"\bback[\s-]?end\b", 15),
    "fullstack": (r"\bfull[\s-]?stack\b", 15),
    "software engineer": (r"\bsoftware (engineer|developer|development engineer)\b|\bsde\b|\bswe\b", 10),
}

# Seniority/level signals in the title.
LEVEL_TITLE: dict[str, tuple[str, int]] = {
    "intern": (r"\bintern(ship)?\b", 30),
    "new grad": (r"\b(new|fresh(er)?)[\s-]?grad(uate)?s?\b", 30),
    "graduate": (r"\bgraduate\b", 20),
    "fresher": (r"\bfreshers?\b", 30),
    "trainee": (r"\btrainee\b|\bapprentice\b", 25),
    "junior": (r"\bjunior\b|\bjr\.?\b", 20),
    "entry level": (r"\bentry[\s-]?level\b", 25),
    "associate": (r"\bassociate\b", 10),
    "level 1": (r"\b(sde|swe|engineer)[\s-]?(1|i)\b", 15),
}

TITLE_MULTIPLIER = 3

# Any hit in the title drops the job outright. Level 2+ ("SDE2", "Engineer II") is mid-level.
TOO_SENIOR_TITLE = (
    r"\b(s[eê]nior|sr\.?|staff|principal|lead|manager|director|head of|vp|vice president|architect"
    r"|intermediate|mid|founding|pleno)\b"
    r"|\b(sde|swe)[\s-]?(2|3|4|ii|iii|iv)\b"
    r"|\b(engineer|developer)[\s,-]*(2|3|4|ii|iii|iv)\b"
)

# Not Max's field, even if a role word slips into the title ("Data Scientist, Cloud ...").
NOT_MY_ROLE_TITLE = (
    r"data scientist|product manager|program manager|project manager|designer|account (executive|manager)"
    r"|\bsales\b|marketing|recruit|customer success|\blegal\b|counsel"
)

# A JD asking for at least this many years of experience is dropped.
DROP_AT_YEARS = 3

# "3+ years of experience", "3-5 yrs relevant experience" / "experience: 5 years".
# Group 1 is the minimum years asked for.
EXPERIENCE_PATTERNS = (
    r"(\d{1,2})\s*(?:\+|plus)?\s*(?:(?:-|–|to)\s*\d{1,2}\s*)?\+?\s*(?:years?|yrs?)\b(?:\s+[\w-]+){0,4}?\s+experience",
    r"experience\s*[:\-–]?\s*(?:of\s+)?(?:minimum\s+|at least\s+)?(\d{1,2})\s*\+?\s*(?:years?|yrs?)\b",
)

# Location passes if it hits any of these, or if it says nothing beyond a country we accept.
LOCATION_OK = r"remote|anywhere|work from home|\bwfh\b|bengaluru|bangalore|chennai"
# A bare country with no city ("India") is kept: it may well be remote or Bengaluru.
LOCATION_COUNTRY_ONLY_OK = r"^\s*(india|in)\s*$"

# Max's stack (from his resume, plus k8s & friends). Matched case-insensitively against the JD;
# `(?-i:...)` marks the parts that must match case exactly (Go, REST, React, SOPS).
TECHS: dict[str, tuple[str, int]] = {
    "go": (r"\bgolang\b|(?-i:(?:(?<=[,/(])|(?<=[,/(]\s))Go\b|\bGo(?=\s*[,/)]|\s+(?:and|or)\b))", 6),
    "python": (r"\bpython\b", 6),
    "shell": (r"\bbash\b|\bshell script(ing|s)?\b", 3),
    "javascript": (r"\bjavascript\b", 3),
    "typescript": (r"\btypescript\b", 3),
    "c++": (r"\bc\+\+", 2),
    "fastapi": (r"\bfastapi\b", 5),
    "rest": (r"(?-i:\bREST(ful)?\b)", 2),
    "postgresql": (r"\bpostgres(ql)?\b", 5),
    "redis": (r"\bredis\b", 4),
    "supabase": (r"\bsupabase\b", 3),
    "graphql": (r"\bgraphql\b", 3),
    "react": (r"(?-i:\bReact(\.js|js)?\b)", 3),
    "tailwind": (r"\btailwind\b", 2),
    "vite": (r"\bvite\b", 1),
    "linux": (r"\blinux\b", 5),
    "docker": (r"\bdocker\b", 6),
    "docker compose": (r"\bdocker[\s-]compose\b", 3),
    "kubernetes": (r"\bkubernetes\b|\bk8s\b", 6),
    "helm": (r"\bhelm\b", 4),
    "terraform": (r"\bterraform\b|\bopentofu\b", 6),
    "proxmox": (r"\bproxmox\b", 3),
    "nginx": (r"\bnginx\b", 4),
    "cloudflare": (r"\bcloudflare\b", 2),
    "github actions": (r"\bgithub actions\b", 5),
    "ci/cd": (r"\bci\s*/\s*cd\b|\bcicd\b|continuous (integration|delivery|deployment)", 5),
    "sops": (r"(?-i:\bSOPS\b)", 3),
    "git": (r"\bgit\b", 2),
    "aws": (r"\baws\b|amazon web services", 4),
    "gcp": (r"\bgcp\b|google cloud", 4),
    "azure": (r"\bazure\b", 3),
    "prometheus": (r"\bprometheus\b", 4),
    "grafana": (r"\bgrafana\b", 4),
    "observability": (r"\bobservability\b", 3),
}

# Techs found after a requirements-style heading count this many times over.
REQUIREMENTS_MULTIPLIER = 2
REQUIREMENTS_HEADING = (
    r"(?im)^\s*(requirements|qualifications|basic qualifications|minimum qualifications|"
    r"what you('|’)ll need|what we('|’)re looking for|what we require|must[\s-]haves?|"
    r"you have|who you are|skills)\b"
)

# Fresher-friendly signals in the JD body.
LEVEL_DESCRIPTION: dict[str, tuple[str, int]] = {
    "2027 batch": (r"\b2027\b[\s-]*(batch|grad|graduat|pass)", 30),
    "2026 batch": (r"\b2026\b[\s-]*(batch|grad|graduat|pass)", 20),
    "0-2 yrs": (r"\b0\s*(-|–|to)\s*[12]\s*(years?|yrs?)\b", 20),
    "freshers welcome": (r"\bfreshers?\b", 20),
    "students ok": (
        r"\bcurrently (pursuing|enrolled)|\bpursuing (a |an )?(b\.?e|b\.?tech|bachelor|degree)",
        20,
    ),
    "new grad": (r"\b(new|recent) grad(uate)?s?\b", 15),
    "no experience needed": (r"\bno (prior )?experience (required|needed)\b", 15),
}

# Techs add at most this much, so a buzzword-heavy JD can't outrank a real internship.
TECH_SCORE_CAP = 60

# First match wins. Region-locked remote ("Remote - USA") gets nothing: usually needs local work rights.
LOCATION_BONUS: tuple[tuple[str, int], ...] = (
    (r"bengaluru|bangalore|chennai|india", 30),
    (r"^remote$|anywhere|worldwide|global|work from home", 15),
)
