// Every user-facing line with personality lives here. Rewrite freely; nothing else needs to change.

export const COPY = {
  loading: [
    "rummaging through 91 job boards rn",
    "bribing the API gods",
    "LinkedIn is side-eyeing us, one sec",
    "reading 8,000 JDs so you don't have to",
    "touching grass while this loads (jk)",
  ],
  loadingSub: "pulling from Greenhouse, Lever, Ashby, LinkedIn, Naukri and friends.",
  empty: { title: "it's giving… nothing.", body: "no jobs match all that. loosen a filter, or touch grass till the next refresh." },
  error: { title: "the server is having a moment.", body: "not you, it's me. the API didn't answer; try again in a minute.", retry: "Try again" },
  vibes: "salary: 🤫 vibes only",
  converted: "(USD, converted)",
  myZone: { label: "my zone: 4–10 LPA", toast: "my zone. 4 to 10 LPA, no delusions." },
  applied: { stamp: "SENT IT", toast: "filed under Receipts. we keep the evidence." },
  unsent: "un-sent. pretend that never happened.",
  saveFailed: "couldn't save that. the server said: ",
  gate: {
    title: "Members only.",
    body: "it's a one-person club. say the word.",
    label: "Passphrase",
    button: "Let me in",
    wrong: "not it. try the other one.",
    checking: "checking the list…",
  },
  wanted: "interns and fresh grads for SRE, DevOps, platform, cloud, backend and fullstack.",
  where: "Bengaluru, Chennai, India remote, or remote from anywhere.",
  noHr: "HR is in witness protection. couldn't find em.",
  noJd: "they posted a job with no description. bold. mysterious. sus.",
} as const;

/** Status words as Max sees them (the API uses snake_case). */
export const STATUS_LABEL: Record<string, string> = {
  new: "new", applied: "applied", emailed: "emailed", heard_back: "heard back", interview: "interview",
  offer: "offer", rejected: "rejected", ghosted: "ghosted", skipped: "skipped",
};
