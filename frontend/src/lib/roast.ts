// The roast under "My stats.": real counts in, honest abuse out. `hot` is the part that gets the ink.
import type { ReceiptStats } from "./types";

export interface RoastLine { before: string; hot: string; after: string }

/** What 200 applications usually looks like, for the "simulate" toggle. */
export const SIMULATED: ReceiptStats = { sent: 200, emailed: 61, replies: 11, interviews: 2, offers: 0, rejected: 44, ghosted: 143 };

/** The word on the rubber stamp: how done you are. */
export function grade(s: ReceiptStats): string {
  if (s.offers > 0) return "HIRED?!";
  if (s.sent >= 150) return "COOKED";
  if (s.sent >= 40) return "MEDIUM RARE";
  return s.sent > 0 ? "RAW" : "UNOPENED";
}

const plural =(n: number, one: string, many: string) => (n === 1 ? one : many);

export function roastLines(s: ReceiptStats): RoastLine[] {
  if (s.sent === 0) return [{ before: "", hot: "zero applications.", after: " bold strategy. let's see if it pays off." }];

  const lines: RoastLine[] = [];
  if (s.offers > 0) lines.push({ before: `${s.sent} sent, `, hot: `${s.offers} ${plural(s.offers, "offer", "offers")}`, after: ". who are you??" });
  else if (s.sent >= 150) lines.push({ before: `${s.sent} applications, 0 offers. `, hot: "cooked.", after: " fully cooked." });
  else if (s.sent >= 40) lines.push({ before: `${s.sent} applications, 0 offers. `, hot: "medium rare", after: ", keep going." });
  else lines.push({ before: `${s.sent} applications, 0 offers. `, hot: "barely seasoned.", after: " send more." });

  if (s.ghosted > 0) {
    lines.push({ before: `${s.ghosted} ${plural(s.ghosted, "company", "companies")} ghosted you. `, hot: "not even an auto-reply.", after: "" });
  }

  const rate = Math.round((s.replies / s.sent) * 100);
  lines.push(
    rate < 10 ? { before: `${rate}% reply rate. `, hot: "the market is cooked", after: ", not you (mostly)." }
    : rate < 30 ? { before: `${rate}% reply rate. `, hot: "they're noticing.", after: " slowly." }
    : { before: `${rate}% reply rate. `, hot: "you're him.", after: "" },
  );

  if (s.interviews > 0 && s.offers === 0) {
    lines.push({ before: `${s.interviews} ${plural(s.interviews, "interview", "interviews")} in play. `, hot: "lock in.", after: "" });
  }
  if (s.rejected > 0) lines.push({ before: `${s.rejected} said no. `, hot: "their loss.", after: "" });
  return lines.slice(0, 4);
}
