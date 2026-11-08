import { describe, expect, it } from "vitest";
import { findFlags, parseJd } from "./jd";

describe("parseJd", () => {
  it("turns short lines into headings, bullet runs into one list, and the rest into paragraphs", () => {
    const text = "Who you are\n\n• Ambitious builder: you build.\n• Rigorous thinker.\n\nWe ship to millions of people, every day.";
    expect(parseJd(text)).toEqual([
      { kind: "heading", text: "Who you are" },
      { kind: "list", items: ["Ambitious builder: you build.", "Rigorous thinker."] },
      { kind: "paragraph", text: "We ship to millions of people, every day." },
    ]);
  });

  it("copes with no description at all", () => {
    expect(parseJd(null)).toEqual([]);
    expect(parseJd("   ")).toEqual([]);
  });
});

describe("findFlags", () => {
  it("finds each flag once, with the phrase as it appears and an honest translation", () => {
    const flags = findFlags("We value mentorship. A Bachelor's degree is required. Fast-paced team with ownership.");
    const byQuote = Object.fromEntries(flags.map((f) => [f.quote.toLowerCase(), f.tone]));
    expect(byQuote).toMatchObject({ mentor: "green", bachelor: "amber", "fast-paced": "red", ownership: "red" });
    expect(flags.every((f) => f.says.length > 0)).toBe(true);
  });

  it("calls out a hidden years requirement", () => {
    expect(findFlags("You have 3+ years of experience.").map((f) => f.tone)).toContain("red");
  });
});
