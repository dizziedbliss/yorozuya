import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setPassphrase } from "../lib/api";
import { RUN, fakeApi, job, renderWith } from "../test/fakeApi";
import { Fresher } from "./Fresher";

beforeEach(() => setPassphrase("p"));
afterEach(() => vi.unstubAllGlobals());

const JOBS = [job(), job({ id: 2, title: "Software Engineer, New Grad", company: "Stripe", location: "Bangalore", score: 156, salary_min_lpa: 216, salary_max_lpa: 272.3 })];

it("lists the jobs as tickets, best first, with score, company and pay", async () => {
  fakeApi({ "GET /fresher/jobs": { total: 2, jobs: JOBS }, "GET /logs/runs": { runs: [RUN] } });
  renderWith(<Fresher />);

  const [first, second, ...rest] = await screen.findAllByRole("article");
  if (!first || !second) throw new Error("expected two tickets");
  expect(rest).toHaveLength(0);
  expect(within(first).getByText("240")).toBeInTheDocument();
  expect(within(first).getByText(/vibes only/)).toBeInTheDocument();
  expect(within(second).getByText("Stripe")).toBeInTheDocument();
  expect(within(second).getByText("₹2.2–2.7 Cr")).toBeInTheDocument();
  expect(screen.getByText("Last refresh:").parentElement).toHaveTextContent(/43 new, 1 board had trouble/);
});

it("marking a job applied saves it and stamps the ticket", async () => {
  const calls = fakeApi({
    "GET /fresher/jobs": { total: 1, jobs: [job()] },
    "GET /logs/runs": { runs: [RUN] },
    "PATCH /fresher/jobs/1/status": { job_id: 1, status: "applied", note: null, updated_at: "2026-11-08T00:00:00Z" },
  });
  renderWith(<Fresher />);

  await userEvent.click(await screen.findByRole("button", { name: /mark applied/i }));

  expect(calls.find((c) => c.method === "PATCH")?.body).toEqual({ status: "applied", note: null });
  expect(await screen.findByText("SENT IT", { selector: ".stamp" })).toBeInTheDocument();
  expect(screen.getByRole("status", { name: "Notifications" })).toHaveTextContent(/filed under Receipts/i);
});

it("a place chip refetches the list for that place", async () => {
  const calls = fakeApi({ "GET /fresher/jobs": { total: 0, jobs: [] }, "GET /logs/runs": { runs: [RUN] } });
  renderWith(<Fresher />);

  await userEvent.click(await screen.findByRole("button", { name: "Bengaluru" }));

  await screen.findByRole("button", { name: "Bengaluru", pressed: true });
  const last = calls.filter((c) => c.url.pathname === "/fresher/jobs").at(-1);
  expect(last?.url.searchParams.getAll("where")).toEqual(["bengaluru"]);
});

it("says so, in its own voice, when nothing matches", async () => {
  fakeApi({ "GET /fresher/jobs": { total: 0, jobs: [] }, "GET /logs/runs": { runs: [RUN] } });
  renderWith(<Fresher />);
  expect(await screen.findByText(/it's giving… nothing/)).toBeInTheDocument();
});

it("shows the error and a way to retry when the API is down", async () => {
  fakeApi({ "GET /fresher/jobs": () => ({ status: 500, body: { detail: "boom" } }), "GET /logs/runs": { runs: [RUN] } });
  renderWith(<Fresher />);
  expect(await screen.findByText(/the server is having a moment/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
});
