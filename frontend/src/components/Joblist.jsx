import { useState, useEffect } from "react";


function JobItem({ job }) {
    const [isExpanded, setIsExpanded] = useState(false);
    const description = job.description || "";

    return (
        <div className="job-item border-b-2 border-secondary py-2 flex flex-row justify-between items-center">
            <div className="flex items-center mb-2 flex-row">
                <img src={job.logo} alt={job.company} className="w-12 h-12 rounded-full object-cover" />
                <div className="ml-4 mr-10">
                    <p className="font-body text-secondary">{job.company} - {job.location}</p>
                    <h4 className="font-heading text-2xl text-text">{job.title}</h4>

                    <p className="font-body text-secondary mt-1">
                        {isExpanded ? description : `${description.slice(0, 50)}...`}

                        {description.length > 50 && (
                            <button
                                onClick={() => setIsExpanded(!isExpanded)}
                                className="text-accent hover:underline font-semibold ml-2 cursor-pointer text-sm"
                            >
                                {isExpanded ? 'Show Less' : 'Show More'}
                            </button>
                        )}
                    </p>
                </div>
            </div>

            <a
                href={job.applicationLink}
                target="_blank"
                rel="noopener noreferrer"
                className="font-body text-center inline-flex items-center justify-center border-2 border-accent rounded-lg px-4 py-2 hover:bg-accent hover:text-background transition-colors duration-300"
            >
                Apply Now
            </a>
        </div>
    );
}

export default function Joblist() {
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetch("http://localhost:8000/jobs")
            .then(res => res.json())
            .then(data => {
                setJobs(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("fetch system error:",err);
                setError(err.message);
                setLoading(false);
            });
    }, []);


    return (
        <div className="joblist border-2 border-secondary rounded-lg p-4 w-full">
            {jobs.map((job, index) => (
                <JobItem job={job} key={index} />
            ))}

        </div>

    );
}