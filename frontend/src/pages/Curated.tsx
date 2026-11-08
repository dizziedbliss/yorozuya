import { useQuery } from "@tanstack/react-query";
import { useMemo, useRef, useState } from "react";
import { api } from "../lib/api";
import { COPY } from "../lib/copy";
import { useParallax } from "../lib/motion";
import "../styles/curated.css";

const C = COPY.curated;
const PAGE = 40;

export function Curated() {
  const jobs = useQuery({ queryKey: ["curated"], queryFn: api.curated, staleTime: 10 * 60_000 });
  const [q, setQ] = useState("");
  const [company, setCompany] = useState<string | null>(null);
  const [shown, setShown] = useState(PAGE);
  const hero = useRef<HTMLElement>(null);
  useParallax(hero);

  const companies = useMemo(() => {
    const counts = new Map<string, number>();
    for (const j of jobs.data ?? []) counts.set(j.company, (counts.get(j.company) ?? 0) + 1);
    return [...counts].sort((a, b) => b[1] - a[1]);
  }, [jobs.data]);
  const words = q.trim().toLowerCase();
  const matches = (jobs.data ?? []).filter((j) => (!company || j.company === company) && (!words || j.title.toLowerCase().includes(words)));
  const reset = () => setShown(PAGE);

  return (
    <>
      <section className="cposter" ref={hero}>
        <div className="csun" data-depth=".25" aria-hidden="true"><span>{C.sun}</span></div>
        <div className="wrap">
          <h1>{C.title}</h1>
          <p>{C.sub}</p>
        </div>
      </section>

      <div className="wrap cbody">
        {jobs.isPending && <div className="notice loading"><h3>{C.loading}</h3></div>}
        {jobs.isError && (
          <div className="notice"><h3>{COPY.error.title}</h3><p>{jobs.error.message}</p>
            <button className="btn" type="button" onClick={() => void jobs.refetch()}>{COPY.error.retry}</button></div>
        )}
        {jobs.data && (
          <>
            <div className="ctools">
              <input type="search" aria-label={C.search} placeholder={C.search} value={q} onChange={(e) => { setQ(e.target.value); reset(); }} />
              <div className="cchips">
                <button type="button" className="chip" aria-pressed={company === null} onClick={() => { setCompany(null); reset(); }}>{C.all}</button>
                {companies.map(([name, n]) => (
                  <button key={name} type="button" className="chip" aria-pressed={company === name}
                    onClick={() => { setCompany(company === name ? null : name); reset(); }}>{name} <small>{n}</small></button>
                ))}
              </div>
            </div>
            {matches.length === 0 ? (
              <div className="notice"><h3>{COPY.empty.title}</h3><p>{COPY.empty.body}</p></div>
            ) : (
              <>
                <p className="ccount">{C.count(Math.min(shown, matches.length), matches.length)}</p>
                <ol className="clist" aria-label="Curated jobs">
                  {matches.slice(0, shown).map((j, i) => (
                    <li key={j.applicationLink}>
                      <span className="rank">{i + 1}</span>
                      <b className="cscore">{j.score}</b>
                      <div className="cjob">
                        <a href={j.applicationLink} target="_blank" rel="noopener noreferrer">{j.title}</a>
                        <span>{j.company}, {j.location || "location unknown"}</span>
                      </div>
                      <span className="cage">{j.updatedAt.replace(/^1 days\b/, "1 day")}</span>
                    </li>
                  ))}
                </ol>
                {matches.length > shown && (
                  <button className="btn ghost cmore" type="button" onClick={() => setShown(shown + PAGE)}>
                    {C.more(Math.min(PAGE, matches.length - shown))}
                  </button>
                )}
              </>
            )}
          </>
        )}
      </div>
    </>
  );
}
