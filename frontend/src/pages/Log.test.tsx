import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setPassphrase } from "../lib/api";
import type { RunDetail } from "../lib/types";
import { RUN, fakeApi, renderWith } from "../test/fakeApi";
import { Log } from "./Log";

beforeEach(() => setPassphrase("p"));
afterEach(() => vi.unstubAllGlobals());

const OLDER = { ...RUN, id: 0, trigger: "manual", started_at: "2026-11-08T06:17:00Z", total_new: 5, sources: [RUN.sources[0]].flatMap((s) => (s ? [{ ...s, new: 5 }] : [])) };
const DETAIL: RunDetail = { ...RUN, new_jobs: [{ id: 13, title: "Software Engineer, New Grad", company: "Stripe", score: 156 }] };

it("titles the page, grows a ring per run with an arc per board, and lists the schedule", async () => {
  fakeApi({ "GET /logs/runs": { runs: [RUN, OLDER] } });
  renderWith(<Log />, "/log");

  expect(await screen.findByRole("heading", { level: 1 })).toHaveTextContent("Log (a real log)");
  const log = await screen.findByRole("group", { name: /rings of a cut log/i });
  expect(within(log).getAllByRole("button")).toHaveLength(3); // 2 boards in the newest run + 1 in the older one
  expect(within(log).getByRole("button", { name: "jobspy:google, 8 Nov, 18:17, broke" })).toBeInTheDocument();
  const schedule = screen.getByRole("list", { name: "Schedule" });
  expect(within(schedule).getAllByRole("listitem")[0]).toHaveTextContent(/8 Nov, 18:17.*cron.*43 new, 1 broke/);
});

it("zooms an arc into a specimen card with the error, the run's new jobs, and closes on Escape", async () => {
  fakeApi({ "GET /logs/runs": { runs: [RUN] }, "GET /logs/runs/1": DETAIL });
  renderWith(<Log />, "/log");

  const arc = await screen.findByRole("button", { name: /^jobspy:google/ });
  await userEvent.click(arc);
  const card = screen.getByRole("dialog", { name: "jobspy:google." });
  expect(within(card).getByText("no job data returned")).toBeInTheDocument();
  expect(within(card).getByText("6.0 s")).toBeInTheDocument();
  expect(await within(card).findByRole("link", { name: /Software Engineer, New Grad/ })).toHaveAttribute("href", "/jobs/13");

  await userEvent.keyboard("{Escape}");
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(arc).toHaveFocus();
});

it("opens an arc from the keyboard too", async () => {
  fakeApi({ "GET /logs/runs": { runs: [RUN] }, "GET /logs/runs/1": DETAIL });
  renderWith(<Log />, "/log");

  (await screen.findByRole("button", { name: /^greenhouse/ })).focus();
  await userEvent.keyboard("{Enter}");
  expect(screen.getByRole("dialog", { name: "greenhouse." })).toHaveTextContent(/8,243 jobs/);
});

it("says no tree has grown before the first refresh", async () => {
  fakeApi({ "GET /logs/runs": { runs: [] } });
  renderWith(<Log />, "/log");

  expect(await screen.findByText(/no rings yet/i)).toBeInTheDocument();
});
