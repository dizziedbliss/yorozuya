// Mirrors the backend's response models (backend/routers/*.py).

export type Status =
  | "new" | "applied" | "emailed" | "heard_back" | "interview" | "offer" | "rejected" | "ghosted" | "skipped";
export const SENT: readonly Status[] = ["applied", "emailed", "heard_back", "interview", "offer", "rejected", "ghosted"];
export type Where = "bengaluru" | "chennai" | "india" | "remote";

export interface JobCard {
  id: number;
  title: string;
  company: string;
  location: string | null;
  salary_min_lpa: number | null;
  salary_max_lpa: number | null;
  salary_estimated: boolean;
  posted_at: string | null;
  first_seen_at: string;
  score: number;
  matched: string[];
  techs: string[];
  sources: string[];
  status: Status;
  expired: boolean;
  apply_url: string;
}

export interface JobList { total: number; jobs: JobCard[] }

export interface HrContact { email: string; name: string | null; origin: "posting" | "hunter" | "guess"; confidence: number | null }

export interface JobDetail extends JobCard {
  description: string | null;
  note: string | null;
  hr_contacts: HrContact[];
  breakdown: { label: string; points: number }[];
}

export interface FindHr {
  status: "found" | "miss";
  contacts: HrContact[];
  cached: boolean;
  domain: string | null;
  tried: string[];
  hunter_error: string | null;
}

export interface StatusEvent { status: Status; note: string | null; at: string }
export interface Receipt extends JobCard { events: StatusEvent[] }
export interface ReceiptStats { sent: number; emailed: number; replies: number; interviews: number; offers: number; rejected: number; ghosted: number }
export interface Receipts { jobs: Receipt[]; stats: ReceiptStats; activity: { day: string; applied: number }[] }

export interface SourceLine { source: string; status: "ok" | "blocked" | "error"; fetched: number; new: number; error_text: string | null; duration_ms: number | null }
export interface Run { id: number; trigger: string; started_at: string; finished_at: string | null; total_new: number; sources: SourceLine[] }
export interface RunDetail extends Run { new_jobs: { id: number; title: string; company: string; score: number }[] }

export interface JobFilters {
  where?: Where[];
  role?: string[];
  source?: string;
  status?: Status[];
  q?: string;
  salaryMin?: number;
  salaryMax?: number;
  includeNoSalary?: boolean;
  includeExpired?: boolean;
}

/** Curated mode: a live Greenhouse job from the hand-picked list (backend/routers/curated.py). */
export interface CuratedJob { title: string; company: string; location: string; applicationLink: string; logo: string | null; updatedAt: string; score: number }
