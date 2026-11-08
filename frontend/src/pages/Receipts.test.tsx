import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setPassphrase } from "../lib/api";
import type { JobDetail, Receipt, Receipts as ReceiptsData } from "../lib/types";
import { fakeApi, job, renderWith } from "../test/fakeApi";
import { Receipts } from "./Receipts";

beforeEach(() => setPassphrase("p"));
afterEach(() => vi.unstubAllGlobals());

const STRIPE: Receipt = {
  ...job({ id: 13, title: "Software Engineer, New Grad", company: "Stripe", location: "Bangalore", status: "applied" }),
  events: [{ status: "applied", note: "opened the application form", at: "2020-01-02T04:30:00Z" }],
};
const RAZOR: Receipt = {
  ...job({ id: 7, title: "SRE Intern", company: "Razorpay", location: "Bengaluru", status: "heard_back" }),
  events: [
    { status: "applied", note: null, at: "2026-11-01T10:00:00Z" },
    { status: "heard_back", note: "recruiter wants a call", at: "2026-11-07T10:00:00Z" },
  ],
};
const DATA: ReceiptsData = {
  jobs: [RAZOR, STRIPE],
  stats: { sent: 2, emailed: 0, replies: 1, interviews: 0, offers: 0, rejected: 0, ghosted: 0 },
  activity: Array.from({ length: 14 }, (_, i) => ({ day: `2026-11-${String(i + 1).padStart(2, "0")}`, applied: i === 13 ? 2 : 0 })),
};
const DETAIL: JobDetail = { ...STRIPE, description: "Who you are\n\nYou like Kubernetes.", note: null, hr_contacts: [{ email: "jane@stripe.com", name: "Jane Doe", origin: "hunter", confidence: 92 }], breakdown: [] };

it("leads with my stats, a roast, the tally and every receipt line", async () => {
  fakeApi({ "GET /fresher/receipts": DATA });
  renderWith(<Receipts />, "/receipts");

  expect(await screen.findByRole("heading", { level: 1, name: "My stats." })).toBeInTheDocument();
  expect(screen.getByText(/barely seasoned/)).toBeInTheDocument();
  expect(screen.getByText("50% reply rate.", { exact: false })).toBeInTheDocument();
  const tally = screen.getByRole("list", { name: "Tally" });
  expect(within(tally).getByText("2").nextSibling).toHaveTextContent("sent");
  const roll = screen.getByRole("region", { name: "Receipt" });
  expect(within(roll).getAllByRole("button", { name: /^Open / }).map((b) => b.getAttribute("aria-label"))).toEqual([
    "Open SRE Intern at Razorpay", "Open Software Engineer, New Grad at Stripe",
  ]);
  const damage = screen.getByRole("complementary", { name: "Damage report" });
  expect(within(damage).getByRole("img", { name: /ghost rate 0 percent/i })).toBeInTheDocument();
});

it("changes a status with its own reaction, and files it with the server", async () => {
  let server = DATA;
  const calls = fakeApi({
    "GET /fresher/receipts": () => ({ body: server }),
    "PATCH /fresher/jobs/13/status": () => {
      server = { ...DATA, jobs: [RAZOR, { ...STRIPE, status: "ghosted" }], stats: { ...DATA.stats, ghosted: 1 } };
      return { body: { job_id: 13, status: "ghosted", note: "changed on Receipts", updated_at: "2026-11-08T12:00:00Z" } };
    },
  });
  renderWith(<Receipts />, "/receipts");

  await userEvent.selectOptions(await screen.findByRole("combobox", { name: "Status for Software Engineer, New Grad" }), "ghosted");

  expect(screen.getByRole("status", { name: "Notifications" })).toHaveTextContent(/GHOSTED/);
  const line = screen.getByRole("button", { name: "Open Software Engineer, New Grad at Stripe" }).closest(".rline");
  expect(line).toHaveAttribute("data-status", "ghosted");
  await waitFor(() => expect(calls.find((c) => c.method === "PATCH")?.body).toEqual({ status: "ghosted", note: "changed on Receipts" }));
  expect(await screen.findByText(/1 company ghosted you/)).toBeInTheDocument(); // the stats come back from the server
});

it("puts the status back and says why when the server refuses", async () => {
  fakeApi({
    "GET /fresher/receipts": DATA,
    "PATCH /fresher/jobs/13/status": () => ({ status: 500, body: { detail: "database is napping" } }),
  });
  renderWith(<Receipts />, "/receipts");

  const select = await screen.findByRole("combobox", { name: "Status for Software Engineer, New Grad" });
  await userEvent.selectOptions(select, "offer");

  await waitFor(() => expect(screen.getByRole("status", { name: "Notifications" })).toHaveTextContent("database is napping"));
  expect(screen.getByRole("combobox", { name: "Status for Software Engineer, New Grad" })).toHaveValue("applied");
});

it("opens a receipt into its timeline, a follow-up nudge and the JD, and closes on Escape", async () => {
  fakeApi({ "GET /fresher/receipts": DATA, "GET /fresher/jobs/13": DETAIL, "GET /settings": {} });
  renderWith(<Receipts />, "/receipts");

  const line = await screen.findByRole("button", { name: "Open Software Engineer, New Grad at Stripe" });
  await userEvent.click(line);

  const drawer = screen.getByRole("dialog", { name: "Software Engineer, New Grad" });
  const timeline = within(drawer).getByRole("list", { name: "Timeline" });
  expect(within(timeline).getByRole("listitem")).toHaveTextContent(/applied.*opened the application form/);
  expect(within(drawer).getByText(/days of silence/)).toBeInTheDocument();
  const followUp = within(drawer).getByRole("link", { name: /follow-up/i });
  expect(new URL(followUp.getAttribute("href") ?? "").searchParams.get("to")).toBe("jane@stripe.com");
  expect(await within(drawer).findByText("You like Kubernetes.")).toBeInTheDocument();
  expect(within(drawer).getByRole("link", { name: /full poster/i })).toHaveAttribute("href", "/jobs/13");

  await userEvent.keyboard("{Escape}");
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(line).toHaveFocus();
});

it("prints an empty receipt and roasts the empty record", async () => {
  fakeApi({ "GET /fresher/receipts": { jobs: [], stats: { ...DATA.stats, sent: 0, replies: 0 }, activity: DATA.activity } });
  renderWith(<Receipts />, "/receipts");

  expect(await screen.findByText(/zero applications/)).toBeInTheDocument();
  expect(screen.getByText(/nothing printed yet/i)).toBeInTheDocument();
});

it("simulates 200 applications for the vibes, then goes back to the real numbers", async () => {
  fakeApi({ "GET /fresher/receipts": DATA });
  renderWith(<Receipts />, "/receipts");

  const sim = await screen.findByRole("button", { name: /simulate 200 applications/i });
  await userEvent.click(sim);
  expect(sim).toHaveAttribute("aria-pressed", "true");
  expect(within(screen.getByRole("list", { name: "Tally" })).getByText("200")).toBeInTheDocument();
  expect(screen.getByText(/fully cooked/)).toBeInTheDocument();

  await userEvent.click(sim);
  expect(within(screen.getByRole("list", { name: "Tally" })).queryByText("200")).not.toBeInTheDocument();
});
