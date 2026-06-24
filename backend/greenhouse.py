import requests
from helpers import  timestamp_to_days_ago
from os import getenv

LOGO_DEV_PUBLIC_KEY = getenv('LOGO_DEV_PUBLIC_KEY')
# Grouping by algorithmic weight tiers
TITLE_KEYWORDS = {
    # Strong Signals
    "devops": 25,
    "sre": 25,
    "site reliability": 25,

    # Platform Team Signals
    "platform": 15,
    "infrastructure": 15,

    # Medium Signals
    "cloud": 8,
    "operations": 8,
    "production": 8,

    # Niche
    "devsecops": 20,
    "mlops": 15,
    "dataops": 15,
}

CONTENT_KEYWORDS = {

    # Core DevOps Stuff
    "terraform": 10,
    "opentofu": 10,
    "ansible": 8,
    "helm": 8,

    # Reliability
    "prometheus": 8,
    "grafana": 8,
    "datadog": 8,
    "observability": 8,
    "incident response": 8,
    "on-call": 8,

    # CI/CD
    "jenkins": 8,
    "github actions": 8,
    "gitlab ci": 8,
    "cicd": 8,

    # Containers
    "kubernetes": 6,
    "k8s": 6,
    "docker": 4,

    # Cloud
    "aws": 4,
    "azure": 4,
    "gcp": 4,

    # Generic
    "linux": 2,
    "networking": 2,
}

NEGATIVE_TITLE_KEYWORDS = {

    # Leadership
    "manager": -40,
    "director": -60,
    "vp": -80,
    "head of": -80,

    # Too Senior
    "principal": -25,
    "staff": -20,
    "senior": -10,

    # Wrong Field
    "data scientist": -100,
    "product manager": -100,
    "designer": -200,
    "account executive": -200,
    "sales": -200,
    "marketing": -200,
    "hardware": -100,
    "electrical": -100,
    "asic": -100,
    "fpga": -100,
}

negative_content_keywords = {
    "10+ years": -40,
    "8+ years": -30,
    "7+ years": -25,
    "5+ years": -15,
    "3+ years": -5,
}



def final_score(title, content, negative):
      return title*3+content+negative



def get_greenhouse_jobs(company):
    url = f"https://api.greenhouse.io/v1/boards/{company}/jobs?content=true"
    response = requests.get(url)
    if response.status_code != 200:
        return {
            "error": f"Failed to fetch jobs for {company}. Status code: {response.status_code}"
        }

    data = response.json()
    
    jobs = []

    for job in data.get("jobs",[]):
        
        score = 0
        title_score = 0
        content_score = 0
        negative_score = 0
        
        title = job.get("title", "").lower()
        
        for keyword, weight in TITLE_KEYWORDS.items():
            if keyword in title:
                title_score += weight
                    
        content = job.get("content", "").lower()
        
        for keyword, weight in CONTENT_KEYWORDS.items():
            if keyword in content:
                content_score += weight
                
        for keyword, weight in NEGATIVE_TITLE_KEYWORDS.items():
            if keyword in title:
                negative_score += weight
        
        for keyword, weight in negative_content_keywords.items():
            if keyword in content:
                negative_score += weight

        score = final_score(title_score, content_score, negative_score)     
                
        if score > 0:
            jobs.append({
                "title": job.get("title"),
                "company": company,
                "location": job.get("location", {}).get("name"),
                "applicationLink": job.get("absolute_url"),
                "logo":  f"https://img.logo.dev/name/{company}?token={LOGO_DEV_PUBLIC_KEY}",
                "updatedAt": f"{timestamp_to_days_ago(job.get('updated_at'))} days ago",
                "score": score
            })
        
    jobs.sort(key=lambda x: x["score"], reverse=True)
        


    return jobs
