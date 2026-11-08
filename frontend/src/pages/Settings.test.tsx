import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setPassphrase } from "../lib/api";
import { fakeApi, renderWith } from "../test/fakeApi";
import { Settings } from "./Settings";

beforeEach(() => setPassphrase("p"));
afterEach(() => vi.unstubAllGlobals());

const SETTINGS = {
  email_template: { subject: "{role} application", body: "Hi {hr_name}, about {company}." },
  scoring: { min_score: 30, max_age_days: 21 },
  notify: { telegram_min_score: 120, top_n: 5 },
  expiry: { miss_limit: 2, stale_days: 21 },
};
const echo = (key: string) => (_url: URL, init: RequestInit) => ({ body: { key, value: JSON.parse(String(init.body)) } });

it("fills the slip with what's saved and previews the email on a sample job", async () => {
  fakeApi({ "GET /settings": SETTINGS });
  renderWith(<Settings />, "/settings");

  expect(await screen.findByLabelText("Subject")).toHaveValue("{role} application");
  expect(screen.getByLabelText("Body")).toHaveValue("Hi {hr_name}, about {company}.");
  expect(screen.getByLabelText("Lowest score worth showing")).toHaveValue(30);
  const preview = screen.getByRole("complementary", { name: "Preview" });
  expect(preview).toHaveTextContent("Site Reliability Engineer Intern application");
  expect(preview).toHaveTextContent("Hi Priya, about Razorpay.");
});

it("files the template, and a placeholder chip drops in where you'd expect", async () => {
  const calls = fakeApi({ "GET /settings": SETTINGS, "PUT /settings/email_template": echo("email_template") });
  renderWith(<Settings />, "/settings");

  const body = await screen.findByLabelText("Body");
  await userEvent.clear(body);
  await userEvent.type(body, "Yo ");
  await userEvent.click(screen.getByRole("button", { name: "{job_link}" }));
  expect(body).toHaveValue("Yo {job_link}");
  await userEvent.click(screen.getByRole("button", { name: "File the template" }));

  await waitFor(() => expect(calls.find((c) => c.method === "PUT")?.body).toEqual({ subject: "{role} application", body: "Yo {job_link}" }));
  expect(screen.getByRole("status", { name: "Notifications" })).toHaveTextContent(/FILED/);
});

it("saves the numbers without dropping the settings the slip doesn't show", async () => {
  const calls = fakeApi({ "GET /settings": SETTINGS, "PUT /settings/scoring": echo("scoring"), "PUT /settings/expiry": echo("expiry"), "PUT /settings/notify": echo("notify") });
  renderWith(<Settings />, "/settings");

  const min = await screen.findByLabelText("Lowest score worth showing");
  await userEvent.clear(min);
  await userEvent.type(min, "50");
  await userEvent.click(screen.getByRole("button", { name: "File the numbers" }));

  await waitFor(() => expect(calls.filter((c) => c.method === "PUT")).toHaveLength(3));
  expect(calls.find((c) => c.url.pathname === "/settings/scoring")?.body).toEqual({ min_score: 50, max_age_days: 21 });
  expect(calls.find((c) => c.url.pathname === "/settings/expiry")?.body).toEqual({ miss_limit: 2, stale_days: 21 });
});

it("says what the server didn't like", async () => {
  fakeApi({ "GET /settings": SETTINGS, "PUT /settings/email_template": () => ({ status: 422, body: { detail: "subject is too long" } }) });
  renderWith(<Settings />, "/settings");

  await userEvent.click(await screen.findByRole("button", { name: "File the template" }));
  await waitFor(() => expect(screen.getByRole("status", { name: "Notifications" })).toHaveTextContent("subject is too long"));
});

it("won't file an empty subject", async () => {
  const calls = fakeApi({ "GET /settings": SETTINGS });
  renderWith(<Settings />, "/settings");

  await userEvent.clear(await screen.findByLabelText("Subject"));
  const save = screen.getByRole("button", { name: "File the template" });
  expect(save).toBeDisabled();
  expect(within(save.closest("form") ?? document.body).getByText(/needs a subject/i)).toBeInTheDocument();
  expect(calls.some((c) => c.method === "PUT")).toBe(false);
});
