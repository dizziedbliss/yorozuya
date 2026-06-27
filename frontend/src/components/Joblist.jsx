import { useState, useEffect } from "react";
import loadinggif from '../assets/JUSTAWAY.gif';



const API_URL =
    import.meta.env.VITE_API_URL ??
    "http://localhost:8000";

function JobItem({ job }) {

    return (
        <div className="job-item border-t-2 border-secondary px-4">
            <div className="grid grid-cols-8 ">
                <div className="col-span-2  py-2 grid grid-cols-3 border-r-2 border-secondary pr-4" >
                    <img src={job.logo} alt={job.company} className="col-span-1 w-20 h-20 self-center" />
                    <p className="col-start-3 font-body text-body font-bold text-2xl text-right">{job.updatedAt}</p>
                </div>


                <div className="py-2 col-span-6 ml-4 mr-4 grid grid-cols-8 gap-10">
                    <div className="col-span-4 flex flex-col justify-center items-start gap-2">
                        <h4 className="font-body font-bold text-2xl text-body">{job.title}</h4>
                        <a
                            href={job.applicationLink}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-body text-center items-center justify-center border-2 border-accent rounded-lg px-3 py-0.5 hover:bg-accent hover:text-background transition-colors duration-300"
                        >
                            Apply Now
                        </a>

                    </div>
                    <div className="col-span-4 flex flex-col justify-center items-start gap-2">
                        <p className="font-body text-secondary">{job.company} - {job.location}</p>
                    </div>
                </div>



            </div>


        </div>
    );
}

export default function Joblist() {
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetch(`${API_URL}/jobs`)
            .then(res => res.json())
            .then(data => {
                setJobs(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("fetch system error:", err);
                setError(err.message);
                setLoading(false);
            });
    }, []);

    if (loading) {
        return <div className="loading text-center font-black text-2xl p-4 w-full">

            <div className="flex justify-center items-center">
                <img src={loadinggif} alt="Loading... gif" />
            </div>
            <div>Loading...
            </div>
        </div>;
    }
    if (error) {
        return <div className="joblist p-4 w-full">Error: {error}</div>;
    }

    return (
        <div className="joblist p-4 w-full">
            {jobs.map((job, index) => (
                <JobItem job={job} key={index} />
            ))}
        </div>

    );
}