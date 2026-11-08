import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setPassphrase } from "../lib/api";
import type { CuratedJob } from "../lib/types";
import { fakeApi, renderWith } from "../test/fakeApi";
import { Curated } from "./Curated";

beforeEach(() => setPassphrase("p"));
afterEach(() => vi.unstubAllGlobals());

const job = (i: number, over: Partial<CuratedJob> = {}): CuratedJob => ({
  title: `Site Reliability Engineer ${i}`, company: i % 2 ? "GitLab" : "Cloudflare", location: "Remote", logo: null,
  applicationLink: `https://boards.greenhouse.io/x/${i}`, updatedAt: "1 days ago", score: 300 - i, ...over,
});
const JOBS = Array.from({ length: 45 }, (_, i) => job(i));

it("ranks the live list, 40 at a time, each linking out to apply", async () => {
  fakeApi({ "GET /curated/jobs": JOBS });
  renderWith(<Curated />, "/curated");

  expect(await screen.findByRole("heading", { level: 1 })).toHaveTextContent("Curated.");
  const list = await screen.findByRole("list", { name: "Curated jobs" });
  expect(within(list).getAllByRole("listitem")).toHaveLength(40);
  const top = within(list).getAllByRole("listitem")[0];
  expect(top).toHaveTextContent(/1.*300.*Site Reliability Engineer 0.*Cloudflare/);
  expect(within(top ?? document.body).getByRole("link")).toHaveAttribute("href", "https://boards.greenhouse.io/x/0");

  await userEvent.click(screen.getByRole("button", { name: /show 5 more/i }));
  expect(within(list).getAllByRole("listitem")).toHaveLength(45);
});

it("narrows by company and by words in the title", async () => {
  fakeApi({ "GET /curated/jobs": [...JOBS.slice(0, 4), job(99, { title: "Platform Engineer", company: "Stripe" })] });
  renderWith(<Curated />, "/curated");

  await userEvent.click(await screen.findByRole("button", { name: "GitLab 2" }));
  expect(within(screen.getByRole("list", { name: "Curated jobs" })).getAllByRole("listitem")).toHaveLength(2);
  await userEvent.click(screen.getByRole("button", { name: "GitLab 2" }));

  await userEvent.type(screen.getByRole("searchbox", { name: "Search titles" }), "platform");
  const rows = within(screen.getByRole("list", { name: "Curated jobs" })).getAllByRole("listitem");
  expect(rows).toHaveLength(1);
  expect(rows[0]).toHaveTextContent("Stripe");
});

it("says so when nothing matches", async () => {
  fakeApi({ "GET /curated/jobs": JOBS.slice(0, 2) });
  renderWith(<Curated />, "/curated");

  await userEvent.type(await screen.findByRole("searchbox", { name: "Search titles" }), "astronaut");
  expect(screen.getByText(/it's giving… nothing/)).toBeInTheDocument();
});
