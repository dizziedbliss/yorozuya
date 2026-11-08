import { describe, expect, it } from "vitest";
import { PAY_STEPS, formatLpa, payLabel } from "./money";

describe("formatLpa", () => {
  it("shows lakhs below a crore and crores above, rounded like a human would", () => {
    expect(formatLpa(6)).toBe("₹6 LPA");
    expect(formatLpa(7.4)).toBe("₹7 LPA");
    expect(formatLpa(100)).toBe("₹1.0 Cr");
    expect(formatLpa(249.8)).toBe("₹2.5 Cr");
    expect(formatLpa(1200)).toBe("₹12 Cr");
  });
});

describe("payLabel", () => {
  it("says vibes only when there's no pay", () => {
    expect(payLabel(null, null).text).toMatch(/vibes only/);
  });
  it("shows a range, and flags big numbers as converted from USD", () => {
    expect(payLabel(6, 8)).toEqual({ text: "₹6–8 LPA", converted: false });
    expect(payLabel(216, 272.3)).toEqual({ text: "₹2.2–2.7 Cr", converted: true });
    expect(payLabel(12, null)).toEqual({ text: "₹12 LPA", converted: false });
  });
});

describe("PAY_STEPS", () => {
  it("is fine-grained where Max's 4–10 LPA zone lives and ends past the biggest salaries", () => {
    for (const lpa of [4, 5, 6, 7, 8, 10]) expect(PAY_STEPS).toContain(lpa);
    expect(PAY_STEPS[0]).toBe(0);
    expect(PAY_STEPS.at(-1)).toBeGreaterThanOrEqual(500);
  });
});
