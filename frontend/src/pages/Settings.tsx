import { useMutation, useQuery } from "@tanstack/react-query";
import { type ReactNode, useRef, useState } from "react";
import { useToast } from "../components/toast-context";
import { api } from "../lib/api";
import { COPY } from "../lib/copy";
import { type EmailTemplate, fillTemplate, savedTemplate } from "../lib/gmail";
import "../styles/settings.css";

const S = COPY.settings;
const BLANKS = ["{hr_name}", "{company}", "{role}", "{job_link}"] as const;
type AllSettings = Record<string, Record<string, unknown>>;

const num = (group: Record<string, unknown> | undefined, key: string, fallback: number): number => {
  const v = group?.[key];
  return typeof v === "number" ? v : fallback;
};

export function Settings() {
  const settings = useQuery({ queryKey: ["settings"], queryFn: api.settings });

  return (
    <div className="wrap slippage">
      <header className="slipshead">
        <h1>{S.title}</h1>
        <p>{S.sub}</p>
      </header>
      {settings.isPending && <div className="notice loading"><h3>{COPY.loading[1]}</h3></div>}
      {settings.isError && <div className="notice"><h3>{COPY.error.title}</h3><p>{settings.error.message}</p></div>}
      {settings.data && <Slip saved={settings.data} />}
    </div>
  );
}

/** Mounted once the settings are in, so the fields start from what's saved. */
function Slip({ saved }: { saved: AllSettings }) {
  const toast = useToast();
  const [template, setTemplate] = useState<EmailTemplate>(() => savedTemplate(saved));
  const [numbers, setNumbers] = useState(() => ({
    minScore: num(saved.scoring, "min_score", 30),
    maxAge: num(saved.scoring, "max_age_days", 21),
    pingScore: num(saved.notify, "telegram_min_score", 120),
    topN: num(saved.notify, "top_n", 5),
    missLimit: num(saved.expiry, "miss_limit", 2),
  }));
  const body = useRef<HTMLTextAreaElement>(null);
  const [stamped, setStamped] = useState(0);

  const filed = () => { setStamped((n) => n + 1); toast(<><b>{S.filed.stamp}</b> {S.filed.line}</>); };
  const failed = (error: Error) => toast(<>{COPY.saveFailed}{error.message}</>);
  const saveTemplate = useMutation({
    mutationFn: (t: EmailTemplate) => api.saveSetting("email_template", { subject: t.subject, body: t.body }),
    onSuccess: (_data, _vars, _result, context) => { void context.client.invalidateQueries({ queryKey: ["settings"] }); filed(); },
    onError: failed,
  });
  const saveNumbers = useMutation({
    mutationFn: (n: typeof numbers) => Promise.all([
      api.saveSetting("scoring", { ...saved.scoring, min_score: n.minScore, max_age_days: n.maxAge }),
      api.saveSetting("notify", { ...saved.notify, telegram_min_score: n.pingScore, top_n: n.topN }),
      api.saveSetting("expiry", { ...saved.expiry, miss_limit: n.missLimit }),
    ]),
    onSuccess: (_data, _vars, _result, context) => { void context.client.invalidateQueries({ queryKey: ["settings"] }); filed(); },
    onError: failed,
  });

  const drop = (blank: string) => {
    const el = body.current;
    const at = el?.selectionStart ?? template.body.length;
    const end = el?.selectionEnd ?? at;
    setTemplate({ ...template, body: template.body.slice(0, at) + blank + template.body.slice(end) });
    requestAnimationFrame(() => { el?.focus(); el?.setSelectionRange(at + blank.length, at + blank.length); });
  };
  const problem = !template.subject.trim() ? S.noSubject : !template.body.trim() ? S.noBody : null;
  const sample = S.sample;
  const submit = (e: { preventDefault: () => void }, go: () => void) => { e.preventDefault(); go(); };

  return (
    <div className="slipgrid">
    <div className="slip">
      <p className="formno">{S.formNo}</p>
      {stamped > 0 && <div className="filedstamp" key={stamped} aria-hidden="true">FILED</div>}

      <form className="part" aria-labelledby="slip-template" onSubmit={(e) => submit(e, () => { if (!problem) saveTemplate.mutate(template); })}>
        <h2 id="slip-template"><span className="partno">A.</span> {S.template}</h2>
        <Field label="Subject" id="f-subject">
          <input id="f-subject" value={template.subject} maxLength={300} onChange={(e) => setTemplate({ ...template, subject: e.target.value })} />
        </Field>
        <Field label="Body" id="f-body">
          <textarea id="f-body" ref={body} rows={8} value={template.body} onChange={(e) => setTemplate({ ...template, body: e.target.value })} />
        </Field>
        <div className="blanks">
          {BLANKS.map((b) => <button key={b} type="button" className="chip" onClick={() => drop(b)}>{b}</button>)}
        </div>
        <p className="hint">{S.templateHint}</p>
        {problem && <p className="problem" role="alert">{problem}</p>}
        <button className="btn" type="submit" disabled={Boolean(problem) || saveTemplate.isPending}>
          {saveTemplate.isPending ? S.filing : S.fileTemplate}
        </button>
      </form>

      <form className="part" aria-labelledby="slip-numbers" onSubmit={(e) => submit(e, () => saveNumbers.mutate(numbers))}>
        <h2 id="slip-numbers"><span className="partno">B.</span> {S.numbers}</h2>
        <p className="hint">{S.numbersHint}</p>
        <div className="numbers">
          {(Object.keys(S.fields) as (keyof typeof S.fields)[]).map((key) => (
            <Field label={S.fields[key]} id={`f-${key}`} key={key}>
              <input id={`f-${key}`} type="number" inputMode="numeric" min={0} max={key === "maxAge" ? 90 : 999}
                value={numbers[key]} onChange={(e) => setNumbers({ ...numbers, [key]: Number(e.target.value) })} />
            </Field>
          ))}
        </div>
        <button className="btn" type="submit" disabled={saveNumbers.isPending}>{saveNumbers.isPending ? S.filing : S.fileNumbers}</button>
      </form>
    </div>
    <aside className="envelope" aria-label={S.preview}>
      <div className="envhead">
        <span>{S.envelopeTo} {sample.hrName}, {sample.company}</span>
        <span className="postage" aria-hidden="true">✱</span>
      </div>
      <b>{fillTemplate(template.subject, sample)}</b>
      <p>{fillTemplate(template.body, sample)}</p>
      <small>{S.envelopeNote}</small>
    </aside>
    </div>
  );
}

function Field({ label, id, children }: { label: string; id: string; children: ReactNode }) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {children}
    </div>
  );
}
