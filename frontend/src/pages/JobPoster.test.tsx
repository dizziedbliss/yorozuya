import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setPassphrase } from "../lib/api";
import type { JobDetail } from "../lib/types";
import { fakeApi, job, renderWith } from "../test/fakeApi";
import { JobPoster } from "./JobPoster";

beforeEach(() => setPassphrase("p"));
afterEach(() => vi.unstubAllGlobals());

const DETAIL: JobDetail = {
  ...job({ id: 13, title: "Software Engineer, New Grad", company: "Stripe", location: "Bangalore", score: 150 }),
  description: "Who you are\n\n• Ambitious builder.\n• Rigorous thinker.\n\nWe offer mentorship and a Bachelor's degree is required.",
  note: null,
  hr_contacts: [],
  breakdown: [{ label: "role: software engineer", points: 30 }, { label: "level: new grad", points: 90 }, { label: "location: bangalore", points: 30 }],
};
const SETTINGS = { email_template: { subject: "{role} application", body: "Hi {hr_name}, about {company}: {job_link}" } };
const page = () => renderWith(<Routes><Route path="/jobs/:id" element={<JobPoster />} /></Routes>, "/jobs/13");

it("shows the poster, the JD with real lists, why it scored, and the translated flags", async () => {
  fakeApi({ "GET /fresher/jobs/13": DETAIL, "GET /settings": SETTINGS, "GET /fresher/jobs": { total: 1, jobs: [job()] } });
  page();

  expect(await screen.findByRole("heading", { level: 1 })).toHaveTextContent("Software Engineer, New Grad");
  const list = screen.getByRole("list", { name: "" });
  expect(within(list).getAllByRole("listitem").map((li) => li.textContent)).toEqual(["Ambitious builder.", "Rigorous thinker."]);
  const why = screen.getByRole("region", { name: /why 150/i });
  expect(within(why).getByText("level: new grad")).toBeInTheDocument();
  expect(within(why).getByText("+90")).toBeInTheDocument();
  const translator = screen.getByRole("region", { name: /jd translator/i });
  expect(within(translator).getByText(/someone will actually teach you/)).toBeInTheDocument();
  expect(within(translator).getByText(/1 green, 1 amber, 0 red/)).toBeInTheDocument();
});

it("finds HR, then drafts the Gmail from the saved template and marks the job emailed", async () => {
  const calls = fakeApi({
    "GET /fresher/jobs/13": DETAIL, "GET /settings": SETTINGS, "GET /fresher/jobs": { total: 0, jobs: [] },
    "POST /fresher/jobs/13/find-hr": { status: "found", cached: false, domain: "stripe.com", tried: ["posting", "hunter"], hunter_error: null,
      contacts: [{ email: "p.menon@stripe.com", name: "Priya Menon", origin: "hunter", confidence: 85 }] },
    "PATCH /fresher/jobs/13/status": { job_id: 13, status: "emailed", note: null, updated_at: "2026-11-08T00:00:00Z" },
  });
  page();

  await userEvent.click(await screen.findByRole("button", { name: /find hr/i }));
  expect(await screen.findByText("p.menon@stripe.com")).toBeInTheDocument();
  expect(screen.getByText(/found by Hunter, 85% sure/)).toBeInTheDocument();

  const gmail = screen.getByRole("link", { name: /email priya in gmail/i });
  const url = new URL(gmail.getAttribute("href") ?? "");
  expect(url.searchParams.get("to")).toBe("p.menon@stripe.com");
  expect(url.searchParams.get("su")).toBe("Software Engineer, New Grad application");
  expect(url.searchParams.get("body")).toBe("Hi Priya, about Stripe: https://example.com/1");

  await userEvent.click(gmail);
  expect(calls.find((c) => c.method === "PATCH")?.body).toEqual({ status: "emailed", note: "emailed p.menon@stripe.com" });
});

it("says so when HR can't be found", async () => {
  fakeApi({
    "GET /fresher/jobs/13": DETAIL, "GET /settings": SETTINGS, "GET /fresher/jobs": { total: 0, jobs: [] },
    "POST /fresher/jobs/13/find-hr": { status: "miss", cached: false, domain: null, tried: ["posting", "hunter", "guess"], hunter_error: null, contacts: [] },
  });
  page();
  await userEvent.click(await screen.findByRole("button", { name: /find hr/i }));
  expect(await screen.findByText(/witness protection/)).toBeInTheDocument();
});

it("applying on their site marks the job applied", async () => {
  const calls = fakeApi({
    "GET /fresher/jobs/13": DETAIL, "GET /settings": SETTINGS, "GET /fresher/jobs": { total: 0, jobs: [] },
    "PATCH /fresher/jobs/13/status": { job_id: 13, status: "applied", note: null, updated_at: "2026-11-08T00:00:00Z" },
  });
  page();
  await userEvent.click(await screen.findByRole("link", { name: /apply on stripe's site/i }));
  expect(calls.find((c) => c.method === "PATCH")?.body).toEqual({ status: "applied", note: "opened the application form" });
});

it("a job that doesn't exist gets a proper 404", async () => {
  fakeApi({ "GET /fresher/jobs/13": () => ({ status: 404, body: { detail: "job not found" } }), "GET /settings": SETTINGS, "GET /fresher/jobs": { total: 0, jobs: [] } });
  page();
  expect(await screen.findByText(/this job left the building/i)).toBeInTheDocument();
});
