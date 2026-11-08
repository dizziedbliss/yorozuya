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
