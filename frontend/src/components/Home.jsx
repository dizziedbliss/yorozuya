import { useState } from "react";
import yorozuya from '../assets/Yorozuya.jpg'
import Joblist from "./Joblist";

export default function Home() {

  return (
    <div>
      <header className="mt-10">
        <header className="hero font-heading font-bold text-4xl text-center">Welcome to Yorozuya</header>
        <subheader className="hero font-body text-lg mt-4 text-center flex justify-center -translate-y-7 tracking-widest">House of 1000 jobs</subheader>
       
      </header>
      <img src={yorozuya} alt="hero" className="hero-img w-full h-75 object-cover object-center" />
      <div className="flex mt-10 ml-5 mr-5 justify-items-start align-top flex-col"> 
      <h3 className="font-heading text-4xl mb-4 text-accent ">Get a job already!</h3>
      <Joblist />
      </div>
      
    </div>
  );

}