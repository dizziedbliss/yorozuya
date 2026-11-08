import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { getPassphrase, setPassphrase } from "../lib/api";
import { fakeApi, renderWith } from "../test/fakeApi";
import { PassphraseGate } from "./PassphraseGate";

afterEach(() => vi.unstubAllGlobals());

it("asks for the passphrase first and opens once it's right", async () => {
  fakeApi({ "GET /fresher/receipts": (_u: URL, init: RequestInit) =>
    new Headers(init.headers).get("X-Passphrase") === "correct" ? { body: { jobs: [], stats: {}, activity: [] } } : { status: 401, body: { detail: "wrong passphrase" } } });
  renderWith(<PassphraseGate><p>the site</p></PassphraseGate>);

  expect(screen.queryByText("the site")).not.toBeInTheDocument();
  await userEvent.type(screen.getByLabelText(/passphrase/i), "nope");
  await userEvent.click(screen.getByRole("button", { name: /let me in/i }));
  expect(await screen.findByRole("alert")).toHaveTextContent(/not it/i);

  await userEvent.clear(screen.getByLabelText(/passphrase/i));
  await userEvent.type(screen.getByLabelText(/passphrase/i), "correct");
  await userEvent.click(screen.getByRole("button", { name: /let me in/i }));
  expect(await screen.findByText("the site")).toBeInTheDocument();
  expect(getPassphrase()).toBe("correct");
});

it("skips the door when the saved passphrase still works", async () => {
  setPassphrase("correct");
  fakeApi({ "GET /fresher/receipts": { jobs: [], stats: {}, activity: [] } });
  renderWith(<PassphraseGate><p>the site</p></PassphraseGate>);
  expect(await screen.findByText("the site")).toBeInTheDocument();
});
