// "Email in Gmail" opens a pre-filled compose window; Max reads it and hits send himself.

interface Vars { company: string; role: string; hrName: string | null; jobLink: string }

export function fillTemplate(template: string, v: Vars): string {
  const first = v.hrName?.trim().split(/\s+/)[0] || "there";
  return template
    .replaceAll("{hr_name}", first)
    .replaceAll("{company}", v.company)
    .replaceAll("{role}", v.role)
    .replaceAll("{job_link}", v.jobLink);
}

export function composeUrl({ to, subject, body }: { to: string; subject: string; body: string }): string {
  const url = new URL("https://mail.google.com/mail/");
  url.search = new URLSearchParams({ view: "cm", fs: "1", to, su: subject, body }).toString();
  return url.toString();
}

export interface EmailTemplate { subject: string; body: string }

/** Used until Max files his own in Settings. */
export const DEFAULT_TEMPLATE: EmailTemplate = {
  subject: "{role} application",
  body: "Hi {hr_name},\n\nI'd love to be considered for the {role} role at {company} ({job_link}).\n\nThanks,\nAdithya",
};

/** The saved template, if the settings hold a usable one. */
export function savedTemplate(settings: Record<string, Record<string, unknown>> | undefined): EmailTemplate {
  const t = settings?.email_template;
  return typeof t?.subject === "string" && typeof t.body === "string" ? { subject: t.subject, body: t.body } : DEFAULT_TEMPLATE;
}
