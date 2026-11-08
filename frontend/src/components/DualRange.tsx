interface Props {
  steps: readonly number[];
  low: number;
  high: number;
  onChange: (low: number, high: number) => void;
  format: (value: number) => string;
}

/** Two-handle range over discrete steps (indices into `steps`). */
export function DualRange({ steps, low, high, onChange, format }: Props) {
  const top = steps.length - 1;
  const set = (a: number, b: number) => onChange(Math.min(a, b), Math.max(a, b));
  const left = (low / top) * 100;
  const right = (high / top) * 100;
  return (
    <div className="pay">
      <div className="read">
        <span>pay</span>
        <output>{format(steps[low] ?? 0)} to {high === top ? "whatever" : format(steps[high] ?? 0)}</output>
      </div>
      <div className="dual">
        <div className="rail" />
        <div className="fill" style={{ left: `${left}%`, width: `${right - left}%` }} />
        <input type="range" min={0} max={top} step={1} value={low} aria-label="Lowest pay" onChange={(e) => set(Number(e.target.value), high)} />
        <input type="range" min={0} max={top} step={1} value={high} aria-label="Highest pay" onChange={(e) => set(low, Number(e.target.value))} />
      </div>
    </div>
  );
}
