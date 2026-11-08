import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router";
import { vi } from "vitest";
import type { JobCard, Run } from "../lib/types";
import { ToastProvider } from "../components/Toast";

type Handler = (url: URL, init: RequestInit) => { status?: number; body: unknown };
export type Calls = { method: string; url: URL; body: unknown }[];

/** A fetch that answers from `routes` keyed by "METHOD /path"; unknown routes are a 404 so tests fail loudly. */
export function fakeApi(routes: Record<string, Handler | unknown>): Calls {
  const calls: Calls = [];
  vi.stubGlobal("fetch", vi.fn(async (input: string, init: RequestInit = {}) => {
    const url = new URL(input);
    const method = (init.method ?? "GET").toUpperCase();
    calls.push({ method, url, body: init.body ? JSON.parse(String(init.body)) : undefined });
    const route = routes[`${method} ${url.pathname}`];
    if (route === undefined) return new Response(JSON.stringify({ detail: "no fake" }), { status: 404 });
    const answer = typeof route === "function" ? (route as Handler)(url, init) : { body: route };
    return new Response(JSON.stringify(answer.body), { status: answer.status ?? 200, headers: { "Content-Type": "application/json" } });
  }));
  return calls;
}

export function renderWith(ui: ReactNode, path = "/") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <MemoryRouter initialEntries={[path]}>{ui}</MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

export function job(overrides: Partial<JobCard> = {}): JobCard {
  return {
    id: 1, title: "DevOps Intern", company: "Initvalue", location: "Bengaluru, India",
    salary_min_lpa: null, salary_max_lpa: null, salary_estimated: false,
    posted_at: "2026-11-06T00:00:00Z", first_seen_at: "2026-11-08T00:00:00Z",
    score: 240, matched: ["devops", "intern"], techs: ["docker"], sources: ["jsearch"],
    status: "new", expired: false, apply_url: "https://example.com/1", ...overrides,
  };
}

export const RUN: Run = {
  id: 1, trigger: "cron", started_at: "2026-11-08T12:47:00Z", finished_at: "2026-11-08T12:50:00Z", total_new: 43,
  sources: [{ source: "greenhouse", status: "ok", fetched: 8243, new: 13, error_text: null, duration_ms: 128000 },
            { source: "jobspy:google", status: "error", fetched: 0, new: 0, error_text: "no job data returned", duration_ms: 6000 }],
};
