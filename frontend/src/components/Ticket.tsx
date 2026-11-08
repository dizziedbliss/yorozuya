import { Link } from "react-router";
import { COPY } from "../lib/copy";
import { payLabel } from "../lib/money";
import { postedAgo } from "../lib/time";
import { type JobCard, SENT } from "../lib/types";

const LEVELS = new Set(["intern", "new grad", "trainee", "graduate", "junior", "fresher", "entry level", "2027 batch", "2026 batch"]);

interface Props {
  job: JobCard;
  justStamped: boolean;
  onToggleApplied: (job: JobCard, button: HTMLButtonElement) => void;
}

export function Ticket({ job, justStamped, onToggleApplied }: Props) {
  const sent = SENT.includes(job.status);
  const pay = payLabel(job.salary_min_lpa, job.salary_max_lpa);
  const levels = job.matched.filter((m) => LEVELS.has(m));
  const others = job.matched.filter((m) => !LEVELS.has(m));
  return (
    <article className={`ticket${justStamped ? " shake" : ""}${job.expired ? " expired" : ""}`} aria-label={`${job.title} at ${job.company}`}>
      <div className="stub"><div className="score">{job.score}<small>match</small></div></div>
      <div className="tbody">
        <h2 className="role"><Link to={`/jobs/${job.id}`}>{job.title.trim()}</Link></h2>
        <div className="where"><b>{job.company}</b> in {job.location || "somewhere, they didn't say"}</div>
        <div className="tags">
          {[...levels, ...others].map((m) => <span className="tag" key={m}>{m}</span>)}
          {job.techs.map((t) => <span className="tag tech" key={t}>{t}</span>)}
        </div>
        <div className="meta">
          {pay.text === COPY.vibes ? <span>{pay.text}</span> : (
            <span className="money">{pay.text}{pay.converted && <small> {COPY.converted}</small>}</span>
          )}
          <span>{postedAgo(job.posted_at ?? job.first_seen_at)}</span>
          <span>via {job.sources.join(", ")}</span>
        </div>
      </div>
      <div className="actions">
        <Link className="btn" to={`/jobs/${job.id}`}>Open poster</Link>
        <button className="btn ghost" type="button" onClick={(e) => onToggleApplied(job, e.currentTarget)}>
          {sent ? "Unsend" : "Mark applied"}
        </button>
      </div>
      {sent && <div className={`stamp${justStamped ? " thunk" : ""}`} aria-hidden="true">{COPY.applied.stamp}</div>}
    </article>
  );
}
