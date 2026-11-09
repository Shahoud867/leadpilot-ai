import { describe, it, expect, vi, afterEach } from "vitest";
import { api, setCsrf, money, date, nextStages, initials, label } from "./lib";
describe("visible domain contracts", () => {
  it("formats PKR rather than dollars", () =>
    expect(money(65000)).toContain("65,000"));
  it("renders UTC in Pakistan time", () =>
    expect(date("2026-11-08T07:00:00+00:00", true)).toMatch(/12:00/));
  it("does not offer a direct win from assigned", () => {
    expect(nextStages.assigned).not.toContain("won");
    expect(nextStages.appointment).toContain("won");
  });
  it("makes labels and initials readable", () => {
    expect(label("sent_simulated")).toBe("Sent simulated");
    expect(initials("Ayesha Noor")).toBe("AN");
  });
});
describe("API transport", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("sends CSRF and a unique idempotency key for each mutation", async () => {
    setCsrf("csrf-test");
    const fetch = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({ ok: true }) });
    vi.stubGlobal("fetch", fetch);
    await api("/tasks", { action: "send" });
    await api("/tasks", { action: "send" });
    const h = fetch.mock.calls[0][1].headers;
    expect(h["X-CSRF-Token"]).toBe("csrf-test");
    expect(h["Idempotency-Key"]).not.toBe(
      fetch.mock.calls[1][1].headers["Idempotency-Key"],
    );
    expect(fetch.mock.calls[0][1].credentials).toBe("same-origin");
  });
  it("turns structured backend errors into useful text", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({
          detail: [{ loc: ["body", "contact"], msg: "Use SYN identifier" }],
        }),
      }),
    );
    await expect(api("/leads", {})).rejects.toThrow(
      "contact: Use SYN identifier",
    );
  });
  it("reports unreadable responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => {
          throw Error();
        },
      }),
    );
    await expect(api("/leads")).rejects.toThrow("unreadable");
  });
});
