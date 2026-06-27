import { useState } from "react";
import yorozuya from '../assets/Yorozuya.jpg'
import Joblist from "./Joblist";
import Logo from "./logo";

export default function Home() {

  return (
    <div>
      <Logo className="m-5"/>
      <img src={yorozuya} alt="hero" className="hero-img w-full h-75 object-cover object-center" />
      <div className="flex mt-10 ml-5 mr-5 justify-items-start align-top flex-col"> 
      <h3 className="font-heading text-4xl mb-4 text-accent ">Get a job already!</h3>
      <Joblist />
      </div>
      
    </div>
  );

}