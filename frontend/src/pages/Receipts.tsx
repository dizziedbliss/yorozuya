import { useMutation, useQuery } from "@tanstack/react-query";
import { type CSSProperties, useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import { useToast } from "../components/toast-context";
import { api } from "../lib/api";
import { COPY, STATUS_LABEL } from "../lib/copy";
import { composeUrl, fillTemplate } from "../lib/gmail";
import { parseJd } from "../lib/jd";
import { SIMULATED, grade, roastLines } from "../lib/roast";
import { isFxStatus, playStatusFx } from "../lib/statusFx";
import { istStamp } from "../lib/time";
import { type Receipt, type ReceiptStats, type Receipts as ReceiptsData, SENT, type Status } from "../lib/types";
import "../styles/receipts.css";

const R = COPY.receipts;
const DAY = 864e5;
const daysSince = (iso: string, now = Date.now()) => Math.max(0, Math.floor((now - Date.parse(iso)) / DAY));
const SIM_STRIP = [0, 1, 2, 2, 1, 0, 2, 2, 1, 2, 0, 1, 2, 2];

export function Receipts() {
  const toast = useToast();
  const receipts = useQuery({ queryKey: ["receipts"], queryFn: api.receipts });
  const [sim, setSim] = useState(false);
  const [openId, setOpenId] = useState<number | null>(null);
  const lines = useRef(new Map<number, HTMLElement>());
  const opener = useRef<HTMLElement | null>(null);

  const change = useMutation({
    mutationFn: ({ id, status }: { id: number; status: Status }) => api.setStatus(id, status, R.changedNote),
    onMutate: async ({ id, status }, context) => {
      await context.client.cancelQueries({ queryKey: ["receipts"] });
      const before = context.client.getQueryData<ReceiptsData>(["receipts"]);
      const event = { status, note: R.changedNote, at: new Date().toISOString() };
      context.client.setQueryData<ReceiptsData>(["receipts"], (old) =>
        old && { ...old, jobs: old.jobs.map((j) => (j.id === id ? { ...j, status, events: [...j.events, event] } : j)) });
      return { before };
    },
    onError: (error, _vars, result, context) => {
      if (result?.before) context.client.setQueryData(["receipts"], result.before);
      toast(<>{COPY.saveFailed}{error.message}</>);
    },
    onSettled: (_data, _error, { id }, _result, context) => {
      void context.client.invalidateQueries({ queryKey: ["receipts"] });
      void context.client.invalidateQueries({ queryKey: ["jobs"] });
      void context.client.invalidateQueries({ queryKey: ["job", id] });
    },
  });

  if (receipts.isPending) return <div className="wrap" style={{ paddingBlock: 40 }}><div className="notice loading"><h3>{COPY.loading[1]}</h3></div></div>;
  if (receipts.isError) {
    return (
      <div className="wrap" style={{ paddingBlock: 40 }}>
        <div className="notice"><h3>{COPY.error.title}</h3><p>{receipts.error.message}</p>
          <button className="btn" type="button" onClick={() => void receipts.refetch()}>{COPY.error.retry}</button></div>
      </div>
    );
  }

  const { jobs, activity } = receipts.data;
  const stats: ReceiptStats = sim ? SIMULATED : receipts.data.stats;
  const open = jobs.find((j) => j.id === openId);
  const pick = (job: Receipt, next: Status) => {
    if (next === job.status) return;
    change.mutate({ id: job.id, status: next });
    const line = lines.current.get(job.id);
    if (line && isFxStatus(next)) playStatusFx(next, line);
    if (isFxStatus(next)) {
      const { stamp, line: says } = COPY.statusFx[next];
      toast(<><b>{/[.!?]$/.test(stamp) ? stamp : `${stamp}.`}</b> {says}</>);
    }
  };

  return (
    <div className="wrap">
      <header className="rhead">
        <div>
          <h1>{R.title}</h1>
          <div className="roast" key={String(sim)}>
            {roastLines(stats).map((l) => <p key={l.hot}>{l.before}<em>{l.hot}</em>{l.after}</p>)}
          </div>
        </div>
        <div className="rside">
          <div className="rubber" key={grade(stats)} role="img" aria-label={`Graded: ${grade(stats).toLowerCase()}`}>
            <svg viewBox="0 0 200 200" aria-hidden="true">
              <defs><path id="rubber-ring" d="M100,100 m-74,0 a74,74 0 1,1 148,0 a74,74 0 1,1 -148,0" /></defs>
              <circle cx="100" cy="100" r="94" fill="none" stroke="currentColor" strokeWidth="5" />
              <circle cx="100" cy="100" r="58" fill="none" stroke="currentColor" strokeWidth="2.5" />
              <g className="ring"><text><textPath href="#rubber-ring" textLength="462">{R.stampRing}</textPath></text></g>
            </svg>
            <b>{grade(stats)}</b>
          </div>
          <ul className="tally" aria-label="Tally">
            {([["sent", stats.sent], ["replies", stats.replies], ["offers", stats.offers], ["ghosted", stats.ghosted]] as const).map(([label, n]) => (
              <li key={label}><b>{n}</b><span>{label}</span></li>
            ))}
          </ul>
        </div>
        <div className="rtools">
          <button className="chip" type="button" aria-pressed={sim}
            onClick={() => { setSim(!sim); if (!sim) toast(<><b>{R.simToast.stamp}</b> {R.simToast.line}</>); }}>
            {sim ? R.unsimulate : R.simulate}
          </button>
          <span>{sim ? R.simNote : R.realNote}</span>
        </div>
      </header>

      <div className="rbody">
        <section className="roll" aria-label="Receipt">
          <h2>J✱B SEARCH</h2>
          <p className="center">{R.printed} {istStamp(new Date().toISOString())}</p>
          {jobs.length === 0 && (
            <div className="rline empty"><span className="t">{R.empty}</span><span className="d">{R.emptyHint}</span></div>
          )}
          {jobs.map((j) => {
            const age = daysSince(j.events[0]?.at ?? j.first_seen_at);
            return (
              <div className="rline" key={j.id} data-status={j.status}
                ref={(el) => { if (el) lines.current.set(j.id, el); else lines.current.delete(j.id); }}
                onClick={(e) => { if (!(e.target instanceof HTMLSelectElement)) { opener.current = e.currentTarget.querySelector("button"); setOpenId(j.id); } }}>
                <button className="t" type="button" aria-label={`Open ${j.title.trim()} at ${j.company}`}>{j.title.trim()}</button>
                <select aria-label={`Status for ${j.title.trim()}`} value={j.status} onChange={(e) => pick(j, e.target.value as Status)}>
                  {SENT.map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
                </select>
                <span className="d">{j.company}{j.location ? `, ${j.location}` : ""}</span>
                <span className="age">{age === 0 ? "sent today" : `sent ${age}d ago`}</span>
                <span className="stampmark">{(STATUS_LABEL[j.status] ?? j.status).toUpperCase()}</span>
              </div>
            );
          })}
          <div className="rtotal"><span>{R.total}</span><span>{jobs.length}</span></div>
          <div className="barcode" aria-hidden="true" />
          <p className="center">{R.footer}</p>
        </section>

        <DamageReport stats={stats} activity={sim ? activity.map((d, i) => ({ ...d, applied: SIM_STRIP[i] ?? 0 })) : activity} />
      </div>

      {open && <Drawer receipt={open} onClose={() => { setOpenId(null); opener.current?.focus(); }} />}
    </div>
  );
}

function DamageReport({ stats, activity }: { stats: ReceiptStats; activity: ReceiptsData["activity"] }) {
  const funnel: [Status, string, number][] = [
    ["applied", "applied", stats.sent], ["emailed", "emailed", Math.min(stats.emailed, stats.sent)],
    ["heard_back", "heard back", stats.replies], ["interview", "interview", stats.interviews], ["offer", "offer", stats.offers],
  ];
  const ghostRate = stats.sent ? Math.round((stats.ghosted / stats.sent) * 100) : 0;
  const angle = Math.PI * (1 - ghostRate / 100);
  const meter = ghostRate > 50 ? R.ghostMeter.haunted : ghostRate > 15 ? R.ghostMeter.spooky : R.ghostMeter.polite;
  const first = activity[0];
  return (
    <aside className="damage" aria-label={R.damage}>
      <section>
        <h2>{R.damage}</h2>
        <div className="funnel">
          {funnel.map(([status, label, n]) => (
            <div className="fstep" data-status={status} key={status}>
              <span>{label}</span>
              <div className="track"><i style={{ "--w": `${stats.sent ? Math.max(n ? 2 : 0, Math.round((n / stats.sent) * 100)) : 0}%` } as CSSProperties} /></div>
              <b>{n}</b>
            </div>
          ))}
        </div>
      </section>
      <section className="gauge" data-status="ghosted">
        <svg viewBox="0 0 200 116" role="img" aria-label={`Ghost rate ${ghostRate} percent`}>
          <path d="M14 104 A86 86 0 0 1 186 104" fill="none" stroke="var(--paper-2)" strokeWidth="20" />
          <path className="arcfill" d="M14 104 A86 86 0 0 1 186 104" fill="none" stroke="var(--st)" strokeWidth="20" pathLength={100} strokeDasharray={`${ghostRate} 100`} />
          <line className="needle" x1="100" y1="104" x2={100 + 70 * Math.cos(angle)} y2={104 - 70 * Math.sin(angle)} stroke="var(--ink)" strokeWidth="4" strokeLinecap="round" />
          <circle cx="100" cy="104" r="7" fill="var(--ink)" />
        </svg>
        <p><b className="rate">{ghostRate}%</b><br />ghost-o-meter. {meter}</p>
      </section>
      <section>
        <h3>{R.last14}</h3>
        <div className="strip">{activity.map((d) => <i key={d.day} data-n={Math.min(2, d.applied)} title={`${d.day}: ${d.applied} sent`} />)}</div>
        <div className="strip-labels"><span>{first ? new Date(`${first.day}T00:00:00Z`).toLocaleDateString("en-IN", { day: "numeric", month: "short", timeZone: "UTC" }) : ""}</span><span>today</span></div>
      </section>
    </aside>
  );
}

function Drawer({ receipt: j, onClose }: { receipt: Receipt; onClose: () => void }) {
  const detail = useQuery({ queryKey: ["job", j.id], queryFn: () => api.job(j.id) });
  const close = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    close.current?.focus();
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    addEventListener("keydown", onKey);
    return () => removeEventListener("keydown", onKey);
  }, [onClose]);

  const last = j.events.at(-1);
  const quiet = last ? daysSince(last.at) : 0;
  const nudge = (j.status === "applied" || j.status === "emailed") && quiet >= 5;
  const hr = detail.data?.hr_contacts[0];
  const role = j.title.trim();
  const followUp = composeUrl({
    to: hr?.email ?? "",
    subject: `Following up: ${role}`,
    body: fillTemplate("Hi {hr_name},\n\nFollowing up on my application for the {role} role at {company} ({job_link}). Still very keen, and happy to share anything that helps.\n\nThanks,\nAdithya",
      { company: j.company, role, hrName: hr?.name ?? null, jobLink: j.apply_url }),
  });
  const blocks = parseJd(detail.data?.description ?? null).slice(0, 14);

  return (
    <div className="drawer" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="sheet" role="dialog" aria-modal="true" aria-labelledby="drawer-title" data-status={j.status}>
        <div className="sheethead">
          <h2 id="drawer-title">{role}</h2>
          <button className="btn ghost" type="button" ref={close} onClick={onClose}>{R.close}</button>
        </div>
        <p className="sheetmeta">{j.company}{j.location ? `, ${j.location}` : ""}. Score {j.score}. <span className="stampmark">{(STATUS_LABEL[j.status] ?? j.status).toUpperCase()}</span></p>
        {j.events.length === 0 && <p className="sheetmeta">{R.noHistory}</p>}
        <ol className="timeline" aria-label="Timeline" hidden={j.events.length === 0}>
          {j.events.map((e, i) => (
            <li key={`${e.at}-${i}`} data-status={e.status}><time dateTime={e.at}>{istStamp(e.at)}</time><b>{STATUS_LABEL[e.status] ?? e.status}</b>{e.note ? `, ${e.note}` : ""}</li>
          ))}
        </ol>
        {nudge && (
          <div className="nudge"><b>{R.silence(quiet)}</b><span>{R.silenceBody}</span>
            <a className="btn" href={followUp} target="_blank" rel="noopener noreferrer">{R.followUp}</a></div>
        )}
        {j.status === "ghosted" && <div className="nudge gone"><b>{R.gone(quiet)}</b><span>{R.goneBody}</span></div>}
        <Link className="btn ghost" to={`/jobs/${j.id}`}>{R.poster}</Link>
        <div className="excerpt">
          {detail.isPending && <p>{COPY.loading[3]}</p>}
          {detail.isError && <p>{detail.error.message}</p>}
          {detail.data && blocks.length === 0 && <p>{COPY.noJd}</p>}
          {blocks.map((b, i) =>
            b.kind === "heading" ? <h3 key={i}>{b.text}</h3>
            : b.kind === "list" ? <ul key={i}>{b.items.map((item, k) => <li key={k}>{item}</li>)}</ul>
            : <p key={i}>{b.text}</p>,
          )}
        </div>
      </div>
    </div>
  );
}
