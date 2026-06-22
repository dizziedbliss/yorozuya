import { useState } from "react";

export default function Joblist() {
    
  return (
    <div className="joblist border-2 border-secondary rounded-lg p-4 w-full">
        <div className="job-item border-b-2 border-secondary py-2">
            <h4 className="font-heading text-2xl text-body">Job Title </h4>
            <p className="font-body text-secondary">Company Name - Location</p>
        </div>
   
    </div>

  );
}