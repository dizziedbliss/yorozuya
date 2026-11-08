// The Log page draws refresh runs as the rings of a cut log: one ring per run, newest under the bark.
// Pure geometry, so it can be tested without a browser.
import type { Run, SourceLine } from "./types";

export const MAX_RINGS = 30;
export const CENTER = 400;
export const PITH = 40;
export const OUTER = 352;
const GAP = 2.6;
const PAD = 0.012; // radians of bare wood between arcs

export interface Arc { line: SourceLine; a0: number; a1: number; d: string; ink: number }
export interface Ring { run: Run; r0: number; r1: number; arcs: Arc[] }

/** Wood isn't round: one shared wobble so the rings nest, plus a little drift per ring. */
const wobble = (a: number, k: number) =>
  1 + 0.03 * Math.sin(3 * a + 1.1) + 0.016 * Math.sin(5 * a + 0.4) + 0.008 * Math.sin(11 * a + 2.3) + 0.004 * Math.sin(7 * a + k);

const point = (r: number, a: number, k: number): string => {
  const w = r * wobble(a, k);
  return `${(CENTER + w * Math.cos(a)).toFixed(1)} ${(CENTER + w * Math.sin(a)).toFixed(1)}`;
};

/** A closed band between radii r0 and r1, from angle a0 to a1. */
export function band(r0: number, r1: number, a0: number, a1: number, k: number): string {
  const steps = Math.max(4, Math.ceil((a1 - a0) / 0.03));
  const outer: string[] = [];
  const inner: string[] = [];
  for (let s = 0; s <= steps; s++) {
    const a = a0 + ((a1 - a0) * s) / steps;
    outer.push(point(r1, a, k));
    inner.unshift(point(r0, a, k));
  }
  return `M${[...outer, ...inner].join("L")}Z`;
}

/** Runs arrive newest first (as the API sends them); rings come back inside out. */
export function layoutRings(runs: Run[]): { rings: Ring[]; heartwood: number } {
  const kept = runs.slice(0, MAX_RINGS).reverse();
  const width = kept.length ? (OUTER - PITH) / Math.max(kept.length, 8) - GAP : 0;
  const start = OUTER - kept.length * (width + GAP); // newest ring always sits right under the bark
  const rings = kept.map((run, i): Ring => {
    const r0 = start + i * (width + GAP);
    const r1 = r0 + width;
    // a floor so a board that listed nothing (blocked, broken) still gets an arc you can click
    const weights = run.sources.map((l) => Math.max(4, Math.log2(2 + l.fetched)));
    const total = weights.reduce((a, b) => a + b, 0) || 1;
    let a = -Math.PI / 2;
    const arcs = run.sources.map((line, k): Arc => {
      const span = ((weights[k] ?? 0) / total) * Math.PI * 2;
      const arc = { line, a0: a, a1: a + span, d: band(r0, r1, a + PAD, a + span - PAD, i), ink: line.status === "ok" ? 0.3 + 0.7 * Math.min(1, line.new / 6) : 1 };
      a += span;
      return arc;
    });
    return { run, r0, r1, arcs };
  });
  return { rings, heartwood: Math.max(0, runs.length - MAX_RINGS) };
}
