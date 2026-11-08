// Job descriptions arrive as plain text from the backend (headings on their own lines, "• " bullets).

export type JdBlock =
  | { kind: "heading"; text: string }
  | { kind: "paragraph"; text: string }
  | { kind: "list"; items: string[] };

const looksLikeHeading = (line: string) => line.length < 60 && /[a-z]/i.test(line) && !/[.,;!?]$/.test(line);

export function parseJd(text: string | null): JdBlock[] {
  const blocks: JdBlock[] = [];
  for (const raw of (text ?? "").split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    const last = blocks.at(-1);
    if (line.startsWith("• ")) {
      const item = line.slice(2).trim();
      if (last?.kind === "list") last.items.push(item);
      else blocks.push({ kind: "list", items: [item] });
    } else if (looksLikeHeading(line)) {
      blocks.push({ kind: "heading", text: line });
    } else {
      blocks.push({ kind: "paragraph", text: line });
    }
  }
  return blocks;
}

export type Tone = "green" | "amber" | "red";
export interface Flag { quote: string; tone: Tone; says: string }

/** Corporate speak → what it means for a fresher. Edit freely. */
const FLAGS: [RegExp, Tone, string][] = [
  [/mentor/i, "green", "someone will actually teach you. rare W."],
  [/\blearn/i, "green", "they expect you not to know everything yet. good sign."],
  [/new grad|recent graduate|freshers? (are )?welcome/i, "green", "they want people exactly like you. no 5-year trap."],
  [/bachelor|degree/i, "amber", "they care about the degree. yours lands in 2027, say so up front."],
  [/\bgrowth\b/i, "amber", "corporate for: we'll promote you eventually. probably."],
  [/\bimpact\b/i, "amber", "your code ships to real people. scary. cool."],
  [/relocat/i, "amber", "they might move you. pack light."],
  [/fast[- ]paced/i, "red", "chaos, but make it culture."],
  [/ownership/i, "red", "you will be on call."],
  [/competitive (salary|pay|compensation)/i, "red", "they won't say the number."],
  [/wear many hats/i, "red", "three jobs, one salary."],
  [/rockstar|ninja/i, "red", "run."],
  [/\b[3-9]\+?\s*(years|yrs)/i, "red", "that's not a fresher job, chief."],
  [/\bunpaid\b/i, "red", "unpaid. respectfully, no."],
];

export function findFlags(text: string | null): Flag[] {
  const flags: Flag[] = [];
  for (const [pattern, tone, says] of FLAGS) {
    const found = (text ?? "").match(pattern);
    if (found) flags.push({ quote: found[0], tone, says });
  }
  return flags;
}
