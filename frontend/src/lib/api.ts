import type { CuratedJob, FindHr, JobDetail, JobFilters, JobList, Receipts, Run, RunDetail, Status } from "./types";

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";
const KEY = "jbsearch.passphrase";

/** The API said 401: the passphrase is missing or wrong, so the gate should show. */
export class AuthError extends Error {}

export function getPassphrase(): string {
  try {
    return localStorage.getItem(KEY) ?? "";
  } catch {
    return ""; // storage blocked (private mode): the gate will just ask again
  }
}

export function setPassphrase(value: string): void {
  try {
    localStorage.setItem(KEY, value);
  } catch {
    // storage blocked: nothing to persist, the session still works until reload
  }
}

async function request<T>(path: string, init: RequestInit = {}, params?: URLSearchParams): Promise<T> {
  const url = new URL(path, BASE);
  if (params) url.search = params.toString();
  const headers = new Headers(init.headers);
  headers.set("X-Passphrase", getPassphrase());
  if (init.body) headers.set("Content-Type", "application/json");
  const response = await fetch(url.toString(), { ...init, headers });
  if (response.status === 401) throw new AuthError("wrong passphrase");
  if (!response.ok) {
    let reason = `${response.status} ${response.statusText}`.trim();
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") reason = body.detail;
    } catch {
      // not JSON: keep the status line as the reason
    }
    throw new Error(reason);
  }
  return (await response.json()) as T;
}

function jobParams(f: JobFilters): URLSearchParams {
  const p = new URLSearchParams();
  f.where?.forEach((w) => p.append("where", w));
  f.role?.forEach((r) => p.append("role", r));
  f.status?.forEach((s) => p.append("status", s));
  if (f.source) p.set("source", f.source);
  if (f.q) p.set("q", f.q);
  if (f.salaryMin != null) p.set("salary_min", String(f.salaryMin));
  if (f.salaryMax != null) p.set("salary_max", String(f.salaryMax));
  if (f.includeNoSalary != null) p.set("include_no_salary", String(f.includeNoSalary));
  if (f.includeExpired != null) p.set("include_expired", String(f.includeExpired));
  return p;
}

export const api = {
  jobs: (filters: JobFilters) => request<JobList>("/fresher/jobs", {}, jobParams(filters)),
  job: (id: number) => request<JobDetail>(`/fresher/jobs/${id}`),
  setStatus: (id: number, status: Status, note: string | null = null) =>
    request<{ job_id: number; status: Status; note: string | null; updated_at: string }>(`/fresher/jobs/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, note }),
    }),
  findHr: (id: number) => request<FindHr>(`/fresher/jobs/${id}/find-hr`, { method: "POST" }),
  receipts: () => request<Receipts>("/fresher/receipts"),
  curated: () => request<CuratedJob[]>("/curated/jobs"),
  runs: (limit = 40) => request<{ runs: Run[] }>("/logs/runs", {}, new URLSearchParams({ limit: String(limit) })),
  run: (id: number) => request<RunDetail>(`/logs/runs/${id}`),
  settings: () => request<Record<string, Record<string, unknown>>>("/settings"),
  saveSetting: (key: string, value: Record<string, unknown>) =>
    request<{ key: string; value: Record<string, unknown> }>(`/settings/${key}`, { method: "PUT", body: JSON.stringify(value) }),
};
