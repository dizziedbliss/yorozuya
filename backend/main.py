from fastapi import FastAPI

app = FastAPI()


@app.get("/jobs")
async def get_jobs():
    return [
        {
            "title": "Software Engineer",
            "company": "TechCorp",
            "location": "San Francisco, CA",
            "logo": "https://static.cdninstagram.com/rsrc.php/yr/r/rzWiSjZRxk5.webp",
            "applicationLink": "https://techcorp.com/jobs/software-engineer",
            "description": "Join our tfw9ufnwuefnf9ue efiuwe9f9w ehf0ehfwhe0 we9fh0wehf ffhwe0hfw wefhw9ehf wef98h9fheww weefhw0eehf eam of innovative engineers to build cutting-edge software solutions.",
        },
        {
            "title": "Product Manager",
            "company": "InnovateX",
            "location": "New York, NY",
            "logo": "https://via.placeholder.com/50",
            "applicationLink": "https://innovatex.com/jobs/product-manager",
            "description": "Lead our product development loreinidn eiunw wiufnwi we9uwee  ewidudeweunu9ew wiuniweniwn weff9wfiwe weefuwief ewf9ufehf9ueew fw9efw9f9w  efforts and drive innovation.",
        },
        {
            "title": "Data Scientist",
            "company": "DataWorks",
            "location": "Seattle, WA",
            "logo": "https://via.placeholder.com/50",
            "applicationLink": "https://dataworks.com/jobs/data-scientist",
            "description": "Analyze complex datasets to extract meaningful insights.",
        },
        {
            "title": "UX Designer",
            "company": "DesignHub",
            "location": "Austin, TX",
            "logo": "https://via.placeholder.com/50",
            "applicationLink": "https://designhub.com/jobs/ux-designer",
            "description": "Create intuitive and engaging user experiences.",
        },
        {
            "title": "DevOps Engineer",
            "company": "CloudSolutions",
            "location": "Boston, MA",
            "logo": "https://via.placeholder.com/50",
            "applicationLink": "https://cloudsolutions.com/jobs/devops-engineer",
            "description": "Ensure seamless deployment and operation of our cloud infrastructure.",
        },
    ]
