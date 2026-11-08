import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type CSSProperties, type ReactNode, useRef, useState } from "react";
import { Link, useParams } from "react-router";
import { useToast } from "../components/toast-context";
import { api } from "../lib/api";
import { COPY } from "../lib/copy";
import { composeUrl, fillTemplate } from "../lib/gmail";
import { type Flag, findFlags, parseJd } from "../lib/jd";
import { burst, useParallax } from "../lib/motion";
import { type HrContact, type JobDetail, SENT, type Status } from "../lib/types";
import "../styles/poster.css";

const DEFAULT_TEMPLATE = { subject: "{role} application", body: "Hi {hr_name},\n\nI'd love to be considered for the {role} role at {company} ({job_link}).\n\nThanks,\nAdithya" };

export function JobPoster() {
  const id = Number(useParams().id);
  const hero = useRef<HTMLElement>(null);
  const toast = useToast();
  const queryClient = useQueryClient();
  const job = useQuery({ queryKey: ["job", id], queryFn: () => api.job(id), enabled: Number.isFinite(id) });
  const settings = useQuery({ queryKey: ["settings"], queryFn: api.settings });
  const others = useQuery({ queryKey: ["jobs", {}], queryFn: () => api.jobs({}) });
  const hr = useMutation({ mutationFn: () => api.findHr(id) });
  const [allContacts, setAllContacts] = useState(false);
  const status = useMutation({
    mutationFn: ({ next, note }: { next: Status; note: string }) => api.setStatus(id, next, note),
    onSuccess: (saved) => {
      queryClient.setQueryData<JobDetail>(["job", id], (old) => old && { ...old, status: saved.status });
      void queryClient.invalidateQueries({ queryKey: ["receipts"] });
      void queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
    onError: (error) => toast(<>{COPY.saveFailed}{error.message}</>),
  });
  useParallax(hero, [job.data?.id]);

  if (job.isPending) return <div className="wrap" style={{ paddingBlock: 40 }}><div className="notice loading"><h3>{COPY.loading[0]}</h3></div></div>;
  if (job.isError) {
    const missing = /not found/i.test(job.error.message);
    return (
      <div className="wrap" style={{ paddingBlock: 40 }}>
        <div className="notice">
          <h3>{missing ? COPY.poster.missingTitle : COPY.error.title}</h3>
          <p>{missing ? COPY.poster.missingBody : job.error.message}</p>
          <Link className="btn" to="/">{COPY.poster.back}</Link>
        </div>
      </div>
    );
  }

  const j = job.data;
  const flags = findFlags(j.description);
  const blocks = parseJd(j.description);
  const count = (tone: Flag["tone"]) => flags.filter((f) => f.tone === tone).length;
  const verdict = count("red") === 0 && count("green") >= 1 ? COPY.poster.verdict.clean : count("red") > count("green") ? COPY.poster.verdict.caution : COPY.poster.verdict.mixed;
  const maxPart = Math.max(1, ...j.breakdown.map((p) => Math.abs(p.points)));
  const template = (settings.data?.email_template as typeof DEFAULT_TEMPLATE | undefined) ?? DEFAULT_TEMPLATE;
  const contacts = hr.data?.contacts ?? j.hr_contacts;
  const best: HrContact | undefined = contacts[0];
  const firstName = best?.name?.split(/\s+/)[0];
  const subject = fillTemplate(template.subject, { company: j.company, role: j.title.trim(), hrName: best?.name ?? null, jobLink: j.apply_url });
  const body = fillTemplate(template.body, { company: j.company, role: j.title.trim(), hrName: best?.name ?? null, jobLink: j.apply_url });
  const sent = SENT.includes(j.status);

  return (
    <>
      <section className="poster" ref={hero}>
        <div className="sun" data-depth=".35" aria-hidden="true"><span>{j.company}</span></div>
        <svg className="dots" data-depth=".15" aria-hidden="true" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice">
          <defs>
            <pattern id="pht" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="4.5" cy="4.5" r="1.6" fill="currentColor" opacity=".55" /></pattern>
            <radialGradient id="pfade"><stop offset="0" stopColor="#fff" /><stop offset="1" stopColor="#000" /></radialGradient>
            <mask id="pm"><rect width="800" height="600" fill="url(#pfade)" /></mask>
          </defs>
          <rect width="800" height="600" fill="url(#pht)" mask="url(#pm)" />
        </svg>
        <div className="vert">{(j.location || "location unknown").toLowerCase()} / via {j.sources.join(", ")}</div>
        <div className="corner">{j.score}<small>match score</small></div>
        <div className="wrap">
          <h1 className="bigtitle" data-depth="-.08">{j.title.trim()}</h1>
          <div className="sub">at {j.company}{j.location ? `, ${j.location}` : ""}.</div>
          {j.expired && <div className="ghosted">{COPY.poster.vanished}</div>}
        </div>
        <svg className="initial" data-depth=".22" viewBox="0 0 300 300" aria-hidden="true">
          <defs><pattern id="pht2" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(30)"><circle cx="3.5" cy="3.5" r="2.4" fill="var(--red)" /></pattern></defs>
          <text x="150" y="250" textAnchor="middle" fontFamily="Archivo Variable, Arial, sans-serif" fontWeight="900" fontSize="300" fill="url(#pht2)">{j.company.charAt(0).toUpperCase()}</text>
        </svg>
      </section>

      <div className="wrap jd">
        <article>
          {blocks.length === 0 && <p>{COPY.noJd}</p>}
          {blocks.map((b, i) =>
            b.kind === "heading" ? <h2 key={i}>{b.text}</h2>
            : b.kind === "list" ? <ul key={i}>{b.items.map((item, k) => <li key={k}><Marked text={item} flags={flags} /></li>)}</ul>
            : <p key={i}><Marked text={b.text} flags={flags} /></p>,
          )}
        </article>

        <div className="side">
          <aside className="panel" aria-label="Apply">
            <h2>{COPY.poster.shoot}</h2>
            <a className="btn" href={j.apply_url} target="_blank" rel="noopener noreferrer"
              onClick={(e) => {
                if (sent) return;
                status.mutate({ next: "applied", note: "opened the application form" });
                const r = e.currentTarget.getBoundingClientRect();
                burst(r.left + r.width / 2, r.top);
                toast(<><b>{COPY.applied.stamp}.</b> {COPY.poster.appliedToast}</>);
              }}>
              Apply on {j.company}'s site
            </a>
            <button className="btn ghost" type="button" disabled={hr.isPending} onClick={() => hr.mutate()}>
              {hr.isPending ? COPY.poster.asking : hr.data ? (hr.data.contacts.length ? `Found ${hr.data.contacts.length}` : COPY.poster.nobody) : COPY.poster.findHr}
            </button>
            {hr.isError && <p className="origin">{hr.error.message}</p>}
            {hr.data?.hunter_error && <p className="origin">{hr.data.hunter_error}</p>}
            {hr.data?.status === "miss" && <p>{COPY.noHr}</p>}
            {(allContacts ? contacts : contacts.slice(0, 3)).map((c, i) => (
              <div className="contact" key={c.email} style={{ animationDelay: `${i * 90}ms` }}>
                <span>{c.name ?? "Generic inbox"}</span>
                <code>{c.email}</code>
                <span className={`origin ${c.origin}`}>
                  {c.origin === "hunter" ? `found by Hunter, ${c.confidence ?? "?"}% sure` : c.origin === "posting" ? "straight from the posting" : "a guess: the domain takes mail"}
                </span>
              </div>
            ))}
            {contacts.length > 3 && (
              <button className="chip" type="button" onClick={() => setAllContacts(!allContacts)}>
                {allContacts ? "show the top 3" : `show all ${contacts.length}`}
              </button>
            )}
            {best && (
              <>
                <a className="btn" href={composeUrl({ to: best.email, subject, body })} target="_blank" rel="noopener noreferrer"
                  onClick={(e) => {
                    status.mutate({ next: "emailed", note: `emailed ${best.email}` });
                    const r = e.currentTarget.getBoundingClientRect();
                    burst(r.left + r.width / 2, r.top);
                    toast(<><b>{COPY.poster.emailedStamp}.</b> {COPY.poster.emailedToast}</>);
                  }}>
                  Email {firstName ?? "them"} in Gmail
                </a>
                <div className="gmailpreview">{subject}{"\n\n"}{body}</div>
              </>
            )}
          </aside>

          <section className="scorecard" aria-label={`Why ${j.score}?`}>
            <h2>Why {j.score}?</h2>
            {j.breakdown.map((p) => (
              <div className="srow" key={p.label}>
                <span>{p.label}</span>
                <b>{p.points > 0 ? "+" : ""}{p.points}</b>
                <div className="bar"><i style={{ "--w": `${Math.round((Math.abs(p.points) / maxPart) * 100)}%` } as CSSProperties} /></div>
              </div>
            ))}
            <div className="stotal"><span>total</span><span>{j.score}</span></div>
          </section>

          <section className="translator" aria-label="JD translator">
            <h2>JD translator</h2>
            <p className="verdict">{count("green")} green, {count("amber")} amber, {count("red")} red. {verdict}</p>
            {flags.map((f) => (
              <div className={`flag tone-${f.tone}`} key={f.quote}><q>{f.quote}</q><span>{f.says}</span></div>
            ))}
          </section>

          <section className="similar" aria-label="Also hiring">
            <h2>Also hiring</h2>
            {(others.data?.jobs ?? []).filter((o) => o.id !== j.id).slice(0, 3).map((o) => (
              <Link className="mini" key={o.id} to={`/jobs/${o.id}`}><b>{o.score}</b><span>{o.title.trim()}</span><small>{o.company}{o.location ? `, ${o.location}` : ""}</small></Link>
            ))}
          </section>
        </div>
      </div>
    </>
  );
}

/** Underlines the flagged phrases (first match each) inside a line of the JD. */
function Marked({ text, flags }: { text: string; flags: Flag[] }): ReactNode {
  if (!flags.length) return text;
  const pattern = new RegExp(`(${flags.map((f) => f.quote.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "gi");
  return text.split(pattern).map((part, i) => {
    const flag = flags.find((f) => f.quote.toLowerCase() === part.toLowerCase());
    return flag ? <mark key={i} className={`tone-${flag.tone}`}>{part}</mark> : part;
  });
}
