import { describe, expect, it } from "vitest";
import { MAX_RINGS, layoutRings } from "./rings";
import type { Run } from "./types";

const run = (id: number, sources: [string, Run["sources"][number]["status"], number, number][]): Run => ({
  id, trigger: id === 1 ? "manual" : "cron", started_at: `2026-11-0${Math.min(9, id)}T00:17:00Z`, finished_at: null,
  total_new: sources.reduce((n, [, , , fresh]) => n + fresh, 0),
  sources: sources.map(([source, status, fetched, fresh]) => ({ source, status, fetched, new: fresh, error_text: null, duration_ms: null })),
});

describe("layoutRings", () => {
  const runs = [
    run(3, [["greenhouse", "ok", 8000, 9], ["jobspy:linkedin", "blocked", 0, 0], ["remotive", "error", 0, 0]]),
    run(2, [["greenhouse", "ok", 7000, 2]]),
    run(1, [["greenhouse", "ok", 6000, 0]]),
  ];

  it("puts the newest run under the bark and the oldest at the heart", () => {
    const { rings } = layoutRings(runs);
    expect(rings.map((r) => r.run.id)).toEqual([1, 2, 3]); // drawn inside out
    const [oldest, , newest] = rings;
    expect(newest?.r0).toBeGreaterThan(oldest?.r1 ?? Infinity);
  });

  it("gives every source an arc, and the arcs go all the way round", () => {
    const newest = layoutRings(runs).rings.at(-1);
    expect(newest?.arcs.map((a) => [a.line.source, a.line.status])).toEqual([
      ["greenhouse", "ok"], ["jobspy:linkedin", "blocked"], ["remotive", "error"],
    ]);
    const turn = newest?.arcs.reduce((sum, a) => sum + (a.a1 - a.a0), 0) ?? 0;
    expect(turn).toBeCloseTo(Math.PI * 2, 5);
    expect(newest?.arcs[0]?.d).toMatch(/^M[\d. L]+Z$/);
  });

  it("lets a busier board take a longer arc, on a log scale so Greenhouse can't eat the ring", () => {
    const newest = layoutRings(runs).rings.at(-1);
    const span = (i: number) => (newest?.arcs[i]?.a1 ?? 0) - (newest?.arcs[i]?.a0 ?? 0);
    expect(span(0)).toBeGreaterThan(span(1));
    expect(span(0)).toBeLessThan(Math.PI * 1.6);
  });

  it("inks arcs darker when they found more new jobs", () => {
    const rings = layoutRings(runs).rings;
    expect(rings.at(-1)?.arcs[0]?.ink).toBeGreaterThan(rings[0]?.arcs[0]?.ink ?? 1);
  });

  it(`keeps the last ${MAX_RINGS} runs as rings and sinks the rest into the heartwood`, () => {
    const many = Array.from({ length: MAX_RINGS + 7 }, (_, i) => run(100 - i, [["greenhouse", "ok", 10, 1]]));
    const { rings, heartwood } = layoutRings(many);
    expect(rings).toHaveLength(MAX_RINGS);
    expect(heartwood).toBe(7);
    expect(rings.at(-1)?.run.id).toBe(100);
  });

  it("draws nothing for no runs", () => {
    expect(layoutRings([])).toEqual({ rings: [], heartwood: 0 });
  });
});
