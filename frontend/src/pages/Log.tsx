import { useQuery } from "@tanstack/react-query";
import { type CSSProperties, type KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router";
import { api } from "../lib/api";
import { COPY } from "../lib/copy";
import { reducedMotion, useParallax } from "../lib/motion";
import { CENTER, OUTER, PITH, band, layoutRings } from "../lib/rings";
import { istStamp, nextRefresh } from "../lib/time";
import type { Run, SourceLine } from "../lib/types";
import "../styles/log.css";

const L = COPY.log;
const STATUS_WORD: Record<SourceLine["status"], string> = { ok: "ok", blocked: "blocked", error: "broke" };
const FILL: Record<SourceLine["status"], string> = { ok: "var(--tizon-red)", blocked: "url(#hatch)", error: "none" };

interface Picked { run: Run; line: SourceLine; from: SVGPathElement }

export function Log() {
  const runs = useQuery({ queryKey: ["runs"], queryFn: () => api.runs(40) });
  const [picked, setPicked] = useState<Picked | null>(null);
  const page = useRef<HTMLDivElement>(null);
  useParallax(page, [runs.data?.runs.length]);
  const layout = useMemo(() => layoutRings(runs.data?.runs ?? []), [runs.data]);

  const open = (run: Run, line: SourceLine, from: SVGPathElement) => setPicked({ run, line, from });
  const onKey = (e: KeyboardEvent<SVGPathElement>, run: Run, line: SourceLine) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(run, line, e.currentTarget); }
  };

  return (
    <div ref={page}>
      <Forest />
      {!reducedMotion() && <Sawdust />}
      <div className="wrap logpage">
        <header className="logshead">
          <div>
            <h1>{L.title} <small>{L.aside}</small></h1>
            <p>{L.sub}</p>
          </div>
          <p className="next">{L.next(nextRefresh())}</p>
        </header>

        {runs.isPending && <div className="notice loading"><h3>{COPY.loading[0]}</h3></div>}
        {runs.isError && <div className="notice"><h3>{COPY.error.title}</h3><p>{runs.error.message}</p></div>}
        {runs.data?.runs.length === 0 && <div className="notice"><h3>{L.empty}</h3></div>}

        {layout.rings.length > 0 && (
          <div className="logsbody">
            <div className="ringbox">
              <svg viewBox="0 0 800 800" role="group" aria-label="Refresh runs drawn as the rings of a cut log">
                <defs>
                  <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                    <rect width="6" height="6" fill="var(--tizon)" /><line x1="0" y1="0" x2="0" y2="6" stroke="var(--tizon-red)" strokeWidth="2.4" />
                  </pattern>
                </defs>
                <path d={band(0, OUTER + 4, 0, Math.PI * 2, 98)} fill="color-mix(in srgb, var(--wood) 35%, var(--tizon))" />
                <path className="ring" d={band(OUTER + 4, OUTER + 26, 0, Math.PI * 2, 99)} fill="var(--bark)" />
                <path d={band(OUTER + 4, OUTER + 26, 0, Math.PI * 2, 99)} fill="none" stroke="var(--tizon)" strokeWidth="2" strokeDasharray="2 9" opacity=".6" />
                {layout.rings.map((ring, i) => (
                  <g className="ring" key={ring.run.id} style={{ animationDelay: `${i * 45}ms` }}>
                    {ring.arcs.map((arc) => (
                      <path key={arc.line.source} className={`arc ${arc.line.status}`} d={arc.d} fill={FILL[arc.line.status]} fillOpacity={arc.ink}
                        role="button" tabIndex={0} aria-label={`${arc.line.source}, ${istStamp(ring.run.started_at)}, ${STATUS_WORD[arc.line.status]}`}
                        onClick={(e) => open(ring.run, arc.line, e.currentTarget)} onKeyDown={(e) => onKey(e, ring.run, arc.line)} />
                    ))}
                  </g>
                ))}
                <Cracks />
                <ellipse className="ring" cx={CENTER} cy={CENTER} rx={PITH - 12} ry={PITH - 16} fill="var(--tizon-red)" />
                <circle cx={CENTER} cy={CENTER} r="5" fill="var(--tizon-ink)" />
              </svg>
              <div className="legend">
                <span><svg width="22" height="12" aria-hidden="true"><rect width="22" height="12" fill="var(--tizon-red)" /></svg>{L.legend.ok}</span>
                <span><svg width="22" height="12" aria-hidden="true"><rect width="22" height="12" fill="url(#hatch)" stroke="var(--tizon-red)" /></svg>{L.legend.blocked}</span>
                <span><svg width="22" height="12" aria-hidden="true"><rect x="1" y="1" width="20" height="10" fill="none" stroke="var(--tizon-red)" strokeDasharray="3 3" /></svg>{L.legend.error}</span>
              </div>
              <p className="note">{L.note}{layout.heartwood > 0 && ` ${L.heartwood(layout.heartwood)}.`}</p>
            </div>

            <section className="schedule">
              <h2>{L.schedule}</h2>
              <ol aria-label={L.schedule}>
                {(runs.data?.runs ?? []).slice(0, 14).map((run) => {
                  const broke = run.sources.filter((s) => s.status !== "ok").length;
                  return (
                    <li key={run.id}>
                      <span>{istStamp(run.started_at)}</span>
                      <span>{run.trigger}</span>
                      <span><b>{run.total_new}</b> new{broke ? `, ${broke} broke` : ""}</span>
                    </li>
                  );
                })}
              </ol>
            </section>
          </div>
        )}
      </div>
      {picked && <Specimen picked={picked} onClose={() => { picked.from.focus(); setPicked(null); }} />}
    </div>
  );
}

function Specimen({ picked: { run, line }, onClose }: { picked: Picked; onClose: () => void }) {
  const detail = useQuery({ queryKey: ["run", run.id], queryFn: () => api.run(run.id) });
  const close = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    close.current?.focus();
    const onKey = (e: globalThis.KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    addEventListener("keydown", onKey);
    return () => removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="specimen" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="card" role="dialog" aria-modal="true" aria-labelledby="specimen-title" data-status={line.status}>
        <h3 id="specimen-title">{line.source}.</h3>
        <p className="quip">{L.quips[line.status]}</p>
        <dl>
          <dt>run</dt><dd>{istStamp(run.started_at)}, {run.trigger}</dd>
          <dt>listed</dt><dd>{line.fetched.toLocaleString("en-IN")} jobs</dd>
          <dt>new for you</dt><dd>{line.new}</dd>
          {line.duration_ms != null && <><dt>took</dt><dd>{(line.duration_ms / 1000).toFixed(1)} s</dd></>}
        </dl>
        {line.error_text && <div className="err">{line.error_text}</div>}
        <div className="fresh">
          <h4>{L.newFromRun}</h4>
          {detail.data && detail.data.new_jobs.length === 0 && <p>{L.noneNew}</p>}
          {detail.isError && <p>{detail.error.message}</p>}
          {detail.data?.new_jobs.slice(0, 5).map((j) => (
            <Link key={j.id} to={`/jobs/${j.id}`}><b>{j.score}</b> {j.title.trim()}, {j.company}</Link>
          ))}
        </div>
        <button type="button" ref={close} onClick={onClose}>{L.close}</button>
      </div>
    </div>
  );
}

/** Three radial cracks from the pith, like a log left to dry. */
function Cracks() {
  return (
    <>
      {[[0.6, 160], [2.4, 210], [4.1, 120]].map(([a = 0, len = 0]) => {
        let d = `M${CENTER} ${CENTER}`;
        for (let s = 1; s <= 8; s++) {
          const r = (len * s) / 8;
          const aa = a + Math.sin(s * 3 + a) * 0.05;
          d += `L${(CENTER + r * Math.cos(aa)).toFixed(1)} ${(CENTER + r * Math.sin(aa)).toFixed(1)}`;
        }
        return <path key={a} d={d} fill="none" stroke="var(--tizon)" strokeWidth="3" strokeLinecap="round" />;
      })}
    </>
  );
}

const pines = (n: number, w: number, h: number, y0: number, seed: number) =>
  Array.from({ length: n }, (_, i) => {
    const x = i * (1600 / n) + Math.sin(i * seed) * 30;
    const hh = h * (0.7 + 0.3 * Math.abs(Math.sin(i * 1.7 + seed)));
    return `M${x} ${y0} L${x + w / 2} ${y0 - hh} L${x + w} ${y0} Z M${x + w / 2 - 4} ${y0} h8 v18 h-8 Z`;
  }).join(" ");

function Stump({ x, y, w }: { x: number; y: number; w: number }) {
  return (
    <g fill="currentColor">
      <path d={`M${x} ${y} v${w * 0.6} h${w} v-${w * 0.6}`} />
      <ellipse cx={x + w / 2} cy={y} rx={w / 2} ry={w / 6} fill="var(--tizon)" stroke="currentColor" strokeWidth="4" />
      {[0.32, 0.2, 0.09].map((k) => <ellipse key={k} cx={x + w / 2} cy={y} rx={w * k} ry={(w * k) / 3} fill="none" stroke="currentColor" strokeWidth="2" />)}
    </g>
  );
}

function Pile({ x, y, r }: { x: number; y: number; r: number }) {
  return (
    <g>
      {[[0, 0], [2, 0], [4, 0], [1, 1], [3, 1], [2, 2]].map(([c = 0, row = 0]) => {
        const cx = x + c * r + r;
        const cy = y - row * r * 1.7 - r;
        return (
          <g key={`${c}-${row}`}>
            <circle cx={cx} cy={cy} r={r} fill="currentColor" />
            <circle cx={cx} cy={cy} r={r * 0.6} fill="none" stroke="var(--tizon)" strokeWidth="2" />
            <circle cx={cx} cy={cy} r={r * 0.25} fill="none" stroke="var(--tizon)" strokeWidth="2" />
          </g>
        );
      })}
    </g>
  );
}

function Felled({ x, y }: { x: number; y: number }) {
  return (
    <g fill="currentColor">
      <rect x={x} y={y - 34} width="420" height="34" rx="17" />
      <path d={`M${x + 120} ${y - 34} l-30 -50 l10 -4 l30 50 Z M${x + 260} ${y - 34} l25 -40 l9 5 l-24 39 Z`} />
      <ellipse cx={x + 420} cy={y - 17} rx="12" ry="17" fill="var(--tizon)" stroke="currentColor" strokeWidth="4" />
      <path d={`M${x + 330} ${y - 34} l-10 -60 l14 -2 l8 58 Z`} />
      <path d={`M${x + 306} ${y - 104} q18 -18 40 -6 l-10 22 q-14 -8 -30 -16 Z`} />
    </g>
  );
}

/** Three layers of cut forest behind the page, each at its own parallax depth. */
function Forest() {
  return (
    <div className="forest" aria-hidden="true">
      <div className="layer far" data-depth=".03">
        <svg viewBox="0 0 1600 300" preserveAspectRatio="xMidYMax slice"><path d={pines(28, 70, 220, 300, 2.1)} fill="currentColor" /></svg>
      </div>
      <div className="layer mid" data-depth=".07">
        <svg viewBox="0 0 1600 260" preserveAspectRatio="xMidYMax slice">
          <Stump x={80} y={190} w={150} /><Pile x={1180} y={258} r={34} /><Stump x={820} y={200} w={110} />
          <rect y="250" width="1600" height="10" fill="currentColor" />
        </svg>
      </div>
      <div className="layer near" data-depth=".12">
        <svg viewBox="0 0 1600 220" preserveAspectRatio="xMidYMax slice">
          <Felled x={380} y={210} /><Stump x={1380} y={140} w={170} />
          <rect y="208" width="1600" height="12" fill="currentColor" />
        </svg>
      </div>
    </div>
  );
}

/** Sawdust drifting down; positions are fixed per mount so re-renders don't reshuffle it. */
function Sawdust() {
  const [grains] = useState(() => Array.from({ length: 14 }, () => ({
    left: `${Math.random() * 100}vw`, dx: `${Math.random() * 120 - 60}px`,
    duration: `${7 + Math.random() * 9}s`, delay: `${-Math.random() * 12}s`,
  })));
  return (
    <div aria-hidden="true">
      {grains.map((g, i) => <i key={i} className="dust" style={{ left: g.left, "--dx": g.dx, animationDuration: g.duration, animationDelay: g.delay } as CSSProperties} />)}
    </div>
  );
}
