// Salaries arrive in ₹ lakhs per annum (LPA). 100 LPA = ₹1 crore, which is where US salaries land.

/** Slider stops: fine around Max's 4–10 LPA zone, coarse up where converted US salaries live. */
export const PAY_STEPS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 18, 20, 25, 30, 40, 50, 75, 100, 150, 200, 300, 500] as const;

const crore = (lpa: number) => (lpa / 100).toFixed(lpa >= 1000 ? 0 : 1);

export function formatLpa(lpa: number): string {
  return lpa >= 100 ? `₹${crore(lpa)} Cr` : `₹${Math.round(lpa)} LPA`;
}

export function payLabel(min: number | null, max: number | null): { text: string; converted: boolean } {
  if (min == null && max == null) return { text: "salary: 🤫 vibes only", converted: false };
  const lo = min ?? max ?? 0;
  const hi = max ?? min ?? 0;
  const converted = hi >= 100;
  if (lo === hi || max == null || min == null) return { text: formatLpa(lo), converted };
  if (lo >= 100) return { text: `₹${crore(lo)}–${crore(hi)} Cr`, converted };
  if (hi < 100) return { text: `₹${Math.round(lo)}–${Math.round(hi)} LPA`, converted };
  return { text: `${formatLpa(lo)}–${formatLpa(hi)}`, converted };
}
