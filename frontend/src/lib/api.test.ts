import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthError, api, setPassphrase } from "./api";

afterEach(() => vi.unstubAllGlobals());

function stubFetch(status: number, body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("api", () => {
  it("sends the passphrase and repeats list filters as query params", async () => {
    setPassphrase("open sesame");
    const fetchMock = stubFetch(200, { total: 0, jobs: [] });

    await api.jobs({ where: ["bengaluru", "remote"], role: ["sre"], salaryMin: 4, includeNoSalary: false });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const params = new URL(url).searchParams;
    expect(params.getAll("where")).toEqual(["bengaluru", "remote"]);
    expect(params.getAll("role")).toEqual(["sre"]);
    expect(params.get("salary_min")).toBe("4");
    expect(params.get("include_no_salary")).toBe("false");
    expect(new Headers(init.headers).get("X-Passphrase")).toBe("open sesame");
  });

  it("turns a 401 into an AuthError so the gate can show again", async () => {
    stubFetch(401, { detail: "wrong passphrase" });
    await expect(api.jobs({})).rejects.toBeInstanceOf(AuthError);
  });

  it("puts the server's reason into other errors instead of hiding it", async () => {
    stubFetch(503, { detail: "SITE_PASSPHRASE is not configured" });
    await expect(api.jobs({})).rejects.toThrow("SITE_PASSPHRASE is not configured");
  });

  it("sends status changes as JSON", async () => {
    const fetchMock = stubFetch(200, { job_id: 3, status: "applied", note: null, updated_at: "2026-11-08T00:00:00Z" });
    await api.setStatus(3, "applied");
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/fresher\/jobs\/3\/status$/);
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(String(init.body))).toEqual({ status: "applied", note: null });
  });
});
