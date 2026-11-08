import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";
import { DualRange } from "../components/DualRange";
import { Ticket } from "../components/Ticket";
import { useToast } from "../components/toast-context";
import { api } from "../lib/api";
import { COPY } from "../lib/copy";
import { PAY_STEPS, formatLpa } from "../lib/money";
import { burst, reducedMotion, useParallax } from "../lib/motion";
import { istStamp, nextRefresh } from "../lib/time";
import { type JobCard, type JobFilters, type JobList, SENT, type Status, type Where } from "../lib/types";
import "../styles/fresher.css";

const PLACES: { value: Where; label: string }[] = [
  { value: "bengaluru", label: "Bengaluru" },
  { value: "chennai", label: "Chennai" },
  { value: "india", label: "India" },
  { value: "remote", label: "Remote" },
];
const ROLES = ["sre", "devops", "platform", "cloud", "infra", "backend", "fullstack", "software engineer"];
const TOP = PAY_STEPS.length - 1;
const ZONE: [number, number] = [PAY_STEPS.indexOf(4), PAY_STEPS.indexOf(10)];

const toggle = <T,>(list: T[], value: T): T[] => (list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);

export function Fresher() {
  const [where, setWhere] = useState<Where[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [pay, setPay] = useState<[number, number]>([0, TOP]);
  const [unpaid, setUnpaid] = useState(true);
  const [stamped, setStamped] = useState<number | null>(null);
  const toast = useToast();
  const queryClient = useQueryClient();
  const masthead = useRef<HTMLElement>(null);
  useParallax(masthead);

  const filters = useMemo<JobFilters>(() => ({
    where,
    role: roles,
    salaryMin: pay[0] > 0 ? PAY_STEPS[pay[0]] : undefined,
    salaryMax: pay[1] < TOP ? PAY_STEPS[pay[1]] : undefined,
    includeNoSalary: unpaid,
  }), [where, roles, pay, unpaid]);

  const jobs = useQuery({ queryKey: ["jobs", filters], queryFn: () => api.jobs(filters), placeholderData: keepPreviousData });
  const runs = useQuery({ queryKey: ["runs", 1], queryFn: () => api.runs(1) });
  const lastRun = runs.data?.runs[0];

  const mark = useMutation({
    mutationFn: ({ job, status }: { job: JobCard; status: Status }) => api.setStatus(job.id, status),
    onMutate: async ({ job, status }, context) => {
      await context.client.cancelQueries({ queryKey: ["jobs"] });
      const before = context.client.getQueriesData<JobList>({ queryKey: ["jobs"] });
      context.client.setQueriesData<JobList>({ queryKey: ["jobs"] }, (old) =>
        old && { ...old, jobs: old.jobs.map((j) => (j.id === job.id ? { ...j, status } : j)) });
      return { before };
    },
    onError: (error, _vars, result, context) => {
      result?.before.forEach(([key, data]) => context.client.setQueryData(key, data));
      toast(<>{COPY.saveFailed}{error.message}</>);
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["receipts"] });
    },
  });

  const onToggleApplied = (job: JobCard, button: HTMLButtonElement) => {
    if (SENT.includes(job.status)) {
      mark.mutate({ job, status: "new" });
      toast(COPY.unsent);
      return;
    }
    mark.mutate({ job, status: "applied" });
    const r = button.getBoundingClientRect();
    burst(r.left + r.width / 2, r.top + r.height / 2);
    setStamped(job.id);
    toast(<><b>{COPY.applied.stamp}.</b> {COPY.applied.toast}</>);
  };

  useEffect(() => {
    if (stamped == null) return;
    const t = setTimeout(() => setStamped(null), 700);
    return () => clearTimeout(t);
  }, [stamped]);

  const troubled = lastRun?.sources.filter((s) => s.status !== "ok").length ?? 0;
  const topJob = jobs.data?.jobs[0];
  const ticker = [
    lastRun && `${lastRun.total_new} new last refresh`,
    topJob && `${topJob.company} wants a ${topJob.title.trim().toLowerCase()}`,
    troubled ? `${troubled} board${troubled > 1 ? "s" : ""} gave us trouble (we're not mad)` : "every board answered last time",
    `next refresh at ${nextRefresh()}`,
    jobs.data && `${jobs.data.total} jobs on the wall right now`,
  ].filter(Boolean) as string[];

  return (
    <>
      <div className="wrap">
        <section className="masthead" ref={masthead} aria-label="J✱B Search">
          <Collage />
          <h1 className="jb" aria-label="J star B"><span>J</span><span className="star" aria-hidden="true">✱</span><span>B</span></h1>
          <div className="searchword">Search</div>
        </section>
        <div className="fineprint">
          <span><b>Wanted:</b> {COPY.wanted}</span>
          <span><b>Where:</b> {COPY.where}</span>
          <span><b>Last refresh:</b> {lastRun ? `${istStamp(lastRun.started_at)}. ${lastRun.total_new} new${troubled ? `, ${troubled} board${troubled > 1 ? "s" : ""} had trouble` : ""}. ` : "not yet. "}Next one around {nextRefresh()}.</span>
        </div>
      </div>
      <div className="ticker" aria-hidden="true">
        <div className="track">{[0, 1].flatMap((n) => ticker.map((t, i) => <span key={`${n}-${i}`}><i>✱</i>{t}</span>))}</div>
      </div>

      <div className="filters">
        <div className="wrap">
          <div className="group" role="group" aria-label="Where">
            <span className="lbl">where</span>
            {PLACES.map((p) => (
              <button key={p.value} type="button" className="chip" aria-pressed={where.includes(p.value)} onClick={() => setWhere(toggle(where, p.value))}>{p.label}</button>
            ))}
          </div>
          <div className="group" role="group" aria-label="Role">
            <span className="lbl">role</span>
            {ROLES.map((r) => (
              <button key={r} type="button" className="chip" aria-pressed={roles.includes(r)} onClick={() => setRoles(toggle(roles, r))}>{r}</button>
            ))}
          </div>
          <div className="group" style={{ flex: "1 1 280px", maxWidth: 380 }}>
            <DualRange steps={PAY_STEPS} low={pay[0]} high={pay[1]} onChange={(a, b) => setPay([a, b])} format={formatLpa} />
            <button type="button" className="chip zone" aria-pressed={pay[0] === ZONE[0] && pay[1] === ZONE[1]} onClick={() => { setPay(ZONE); toast(<b>{COPY.myZone.toast}</b>); }}>{COPY.myZone.label}</button>
            <button type="button" className="chip" onClick={() => setPay([0, TOP])}>any pay</button>
          </div>
          <label className="toggle" htmlFor="unpaid">
            <input id="unpaid" type="checkbox" checked={unpaid} onChange={(e) => setUnpaid(e.target.checked)} /> show jobs with no salary listed
          </label>
        </div>
      </div>

      <div className="wrap">
        <section className="pad" aria-live="polite" aria-busy={jobs.isFetching}>
          {jobs.isPending ? <Loading /> : jobs.isError ? (
            <div className="notice">
              <h3>{COPY.error.title}</h3>
              <p>{COPY.error.body}</p>
              <button className="btn" type="button" onClick={() => void jobs.refetch()}>{COPY.error.retry}</button>
            </div>
          ) : jobs.data.jobs.length === 0 ? (
            <div className="notice"><h3>{COPY.empty.title}</h3><p>{COPY.empty.body}</p></div>
          ) : (
            jobs.data.jobs.map((job) => <Ticket key={job.id} job={job} justStamped={stamped === job.id} onToggleApplied={onToggleApplied} />)
          )}
        </section>
      </div>
    </>
  );
}

function Loading() {
  const [i, setI] = useState(0);
  useEffect(() => {
    if (reducedMotion()) return;
    const t = setInterval(() => setI((n) => n + 1), 1600);
    return () => clearInterval(t);
  }, []);
  return (
    <>
      <div className="notice loading"><h3>{COPY.loading[i % COPY.loading.length]}</h3><p>{COPY.loadingSub}</p></div>
      <div className="skel" /><div className="skel" />
    </>
  );
}

function Collage() {
  return (
    <div className="collage" aria-hidden="true">
      <div className="layer l-dots" data-depth=".05">
        <svg viewBox="0 0 600 420" preserveAspectRatio="xMidYMid slice">
          <defs>
            <pattern id="ht" width="10" height="10" patternUnits="userSpaceOnUse"><circle cx="5" cy="5" r="1.7" fill="currentColor" opacity=".5" /></pattern>
            <radialGradient id="fade" cx=".6" cy=".45" r=".55"><stop offset="0" stopColor="#fff" /><stop offset="1" stopColor="#000" /></radialGradient>
            <mask id="m"><rect width="600" height="420" fill="url(#fade)" /></mask>
          </defs>
          <rect width="600" height="420" fill="url(#ht)" mask="url(#m)" />
        </svg>
      </div>
      <div className="layer l-sun" data-depth=".22"><span>now hiring<br />fresh grads</span></div>
      <div className="layer l-wanted" data-depth="-.12">WANTED</div>
      <div className="layer l-fall" data-depth=".35">{[..."FRESH"].map((c, i) => <span key={i}>{c}</span>)}</div>
      <div className="layer l-ast a1" data-depth=".5">✱</div>
      <div className="layer l-ast a2" data-depth=".28">✱</div>
      <div className="layer l-ast a3" data-depth=".6">✱</div>
      <div className="layer l-vert" data-depth=".1">est. 2026 / refreshed every 6 hours</div>
    </div>
  );
}
