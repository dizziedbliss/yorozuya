import { describe, expect, it } from "vitest";
import { composeUrl, fillTemplate } from "./gmail";

describe("fillTemplate", () => {
  it("fills every placeholder and says 'there' when the HR name is unknown", () => {
    const t = "Hi {hr_name}, the {role} role at {company} ({job_link}). {role}!";
    expect(fillTemplate(t, { company: "Stripe", role: "New Grad", hrName: null, jobLink: "https://x.io/1" }))
      .toBe("Hi there, the New Grad role at Stripe (https://x.io/1). New Grad!");
    expect(fillTemplate("Hi {hr_name}", { company: "", role: "", hrName: "Priya Menon", jobLink: "" })).toBe("Hi Priya");
  });
});

describe("composeUrl", () => {
  it("builds a Gmail compose link with the fields encoded", () => {
    const url = new URL(composeUrl({ to: "hr@stripe.com", subject: "Hi & bye", body: "line 1\nline 2" }));
    expect(url.origin + url.pathname).toBe("https://mail.google.com/mail/");
    expect(url.searchParams.get("view")).toBe("cm");
    expect(url.searchParams.get("to")).toBe("hr@stripe.com");
    expect(url.searchParams.get("su")).toBe("Hi & bye");
    expect(url.searchParams.get("body")).toBe("line 1\nline 2");
  });
});
