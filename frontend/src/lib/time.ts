// Max reads times in IST; the API speaks UTC.
const IST = "Asia/Kolkata";

export function istStamp(iso: string): string {
  const d = new Date(iso);
  const day = new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short", timeZone: IST }).format(d);
  const time = new Intl.DateTimeFormat("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: IST }).format(d);
  return `${day}, ${time}`;
}

export function postedAgo(iso: string | null, now: number = Date.now()): string {
  if (!iso) return "posted… sometime";
  const days = Math.floor((now - Date.parse(iso)) / 864e5);
  if (days <= 0) return "posted today";
  if (days === 1) return "posted yesterday";
  return `posted ${days} days ago`;
}

/** The refresh cron runs at :17 past every sixth UTC hour. */
export function nextRefresh(now: number = Date.now()): string {
  const d = new Date(now);
  const next = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate(), Math.floor(d.getUTCHours() / 6) * 6, 17));
  while (next.getTime() <= now) next.setUTCHours(next.getUTCHours() + 6);
  return new Intl.DateTimeFormat("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: IST }).format(next);
}
