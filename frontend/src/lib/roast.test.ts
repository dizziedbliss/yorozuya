import { describe, expect, it } from "vitest";
import { type RoastLine, SIMULATED, grade, roastLines } from "./roast";
import type { ReceiptStats } from "./types";

const stats = (s: Partial<ReceiptStats> = {}): ReceiptStats => ({
  sent: 0, emailed: 0, replies: 0, interviews: 0, offers: 0, rejected: 0, ghosted: 0, ...s,
});
const text = (lines: RoastLine[]) => lines.map((l) => `${l.before}${l.hot}${l.after}`);

describe("roastLines", () => {
  it("roasts an empty record", () => {
    expect(text(roastLines(stats()))).toEqual(["zero applications. bold strategy. let's see if it pays off."]);
  });

  it.each([
    [3, "barely seasoned."],
    [40, "medium rare"],
    [200, "cooked."],
  ])("calls %i applications with no offer %s", (sent, hot) => {
    expect(roastLines(stats({ sent }))[0]?.hot).toBe(hot);
  });

  it("celebrates an offer instead of roasting", () => {
    expect(text(roastLines(stats({ sent: 30, replies: 4, offers: 1 })))[0]).toBe("30 sent, 1 offer. who are you??");
  });

  it("counts ghosts, the reply rate, rejections and live interviews", () => {
    const lines = text(roastLines(stats({ sent: 20, replies: 5, interviews: 2, ghosted: 1, rejected: 3 })));
    expect(lines).toContain("1 company ghosted you. not even an auto-reply.");
    expect(lines).toContain("25% reply rate. they're noticing. slowly.");
    expect(lines).toContain("2 interviews in play. lock in.");
    expect(lines).toHaveLength(4); // the rejection line waits its turn; four lines is plenty
  });

  it("never brings up an ex", () => {
    for (const s of [stats(), stats({ sent: 9, ghosted: 9 }), SIMULATED]) {
      expect(text(roastLines(s)).join(" ")).not.toMatch(/\bex\b/i);
    }
  });

  it.each([
    [stats(), "UNOPENED"], [stats({ sent: 5 }), "RAW"], [stats({ sent: 60 }), "MEDIUM RARE"],
    [SIMULATED, "COOKED"], [stats({ sent: 9, offers: 1 }), "HIRED?!"],
  ])("grades the rubber stamp %#", (s, word) => {
    expect(grade(s)).toBe(word);
  });

  it("is fully cooked at 200 simulated applications", () => {
    expect(text(roastLines(SIMULATED))[0]).toBe("200 applications, 0 offers. cooked. fully cooked.");
  });
});
