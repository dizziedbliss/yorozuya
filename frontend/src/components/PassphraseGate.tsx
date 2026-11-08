import { useQuery } from "@tanstack/react-query";
import { type FormEvent, type ReactNode, useEffect, useState } from "react";
import { AuthError, api, getPassphrase, setPassphrase } from "../lib/api";
import { COPY } from "../lib/copy";

/** Locks the whole site behind one passphrase. Re-locks if any request later comes back 401. */
export function PassphraseGate({ children }: { children: ReactNode }) {
  const [locked, setLocked] = useState(() => !getPassphrase());
  const [attempt, setAttempt] = useState(0);
  const [value, setValue] = useState("");
  // A cheap locked request: if it answers, the passphrase is right.
  const probe = useQuery({ queryKey: ["gate", attempt], queryFn: api.receipts, enabled: !locked, retry: false, staleTime: Infinity });

  useEffect(() => {
    const relock = () => setLocked(true);
    addEventListener("jbsearch:auth-lost", relock);
    return () => removeEventListener("jbsearch:auth-lost", relock);
  }, []);

  if (!locked && probe.isSuccess) return <>{children}</>;

  const checking = !locked && probe.isPending;
  const error = locked || !probe.isError ? null : probe.error instanceof AuthError ? COPY.gate.wrong : probe.error.message;
  const submit = (e: FormEvent) => {
    e.preventDefault();
    setPassphrase(value);
    setLocked(false);
    setAttempt((n) => n + 1);
  };

  return (
    <main className="wrap gate">
      <h1>{COPY.gate.title}</h1>
      <p>{COPY.gate.body}</p>
      <form onSubmit={submit}>
        <label htmlFor="passphrase">{COPY.gate.label}</label>
        <input id="passphrase" type="password" autoComplete="current-password" value={value} onChange={(e) => setValue(e.target.value)} required />
        <button className="btn" type="submit" disabled={checking}>{checking ? COPY.gate.checking : COPY.gate.button}</button>
      </form>
      {error && <p role="alert">{error}</p>}
    </main>
  );
}
