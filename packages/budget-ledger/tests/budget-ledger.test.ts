import { describe, it, expect } from "vitest";
import {
  createSqliteLedger,
  resolveCaps,
  dailyWindow,
  inWindow,
  fits,
  type SpendEstimate,
} from "../src/index.js";
import type { RepoRef, LedgerEntry } from "@itpr/shared-types";

const REPO: RepoRef = { owner: "acme", name: "widgets" };
const CAPS = { tokenCap: 1000, dollarCap: 10 };

function estimate(id: string, tokens: number, dollars = 0): SpendEstimate {
  return { id, tokens, dollars, runId: "run-" + id, provider: "mock" };
}

describe("daily-window", () => {
  it("computes UTC day bounds and membership", () => {
    const w = dailyWindow(new Date("2026-07-10T13:00:00Z"));
    expect(w.start).toBe("2026-07-10T00:00:00.000Z");
    expect(w.end).toBe("2026-07-11T00:00:00.000Z");
    expect(w.key).toBe("2026-07-10");
    expect(inWindow(w, "2026-07-10T23:59:59.000Z")).toBe(true);
    expect(inWindow(w, "2026-07-11T00:00:00.000Z")).toBe(false);
  });
});

describe("repo-budget", () => {
  it("applies per-repo overrides over defaults", () => {
    const caps = resolveCaps(REPO, {
      tokenCap: 100,
      dollarCap: 1,
      overrides: { "acme/widgets": { tokenCap: 500 } },
    });
    expect(caps).toEqual({ tokenCap: 500, dollarCap: 1 });
  });
});

describe("fits", () => {
  it("treats cap=0 as unlimited", () => {
    expect(fits({ tokenCap: 0, dollarCap: 0 }, { tokens: 1e9, dollars: 1e9 }, { tokens: 1, dollars: 1 })).toBe(true);
  });
});

describe("sqlite ledger", () => {
  it("records spend and reflects it in the window", async () => {
    const ledger = createSqliteLedger();
    const now = new Date("2026-07-10T10:00:00Z");
    const entry: LedgerEntry = {
      id: "e1",
      repo: REPO,
      runId: "r1",
      provider: "mock",
      tokens: { input: 100, output: 200, total: 300 },
      dollars: 2,
      at: now.toISOString(),
    };
    await ledger.recordSpend(entry);
    const w = await ledger.getWindow(REPO, CAPS, now);
    expect(w.tokensSpent).toBe(300);
    expect(w.dollarsSpent).toBe(2);
    await ledger.close();
  });

  it("reserves under cap and refuses over cap", async () => {
    const ledger = createSqliteLedger();
    const now = new Date("2026-07-10T10:00:00Z");

    const v1 = await ledger.checkAndReserve(REPO, estimate("a", 600), CAPS, now);
    expect(v1.allowed).toBe(true);
    expect(v1.remainingTokens).toBe(400);

    // second reservation would total 1200 > 1000 -> refused, no reservation
    const v2 = await ledger.checkAndReserve(REPO, estimate("b", 600), CAPS, now);
    expect(v2.allowed).toBe(false);
    expect(v2.reason).toContain("token");

    // window still only reflects the first reservation
    const w = await ledger.getWindow(REPO, CAPS, now);
    expect(w.tokensSpent).toBe(600);
    await ledger.close();
  });

  it("resets across daily windows", async () => {
    const ledger = createSqliteLedger();
    const day1 = new Date("2026-07-10T10:00:00Z");
    const day2 = new Date("2026-07-11T10:00:00Z");

    await ledger.checkAndReserve(REPO, estimate("a", 900), CAPS, day1);
    const w1 = await ledger.getWindow(REPO, CAPS, day1);
    expect(w1.tokensSpent).toBe(900);

    // next day: fresh window, spend resets
    const w2 = await ledger.getWindow(REPO, CAPS, day2);
    expect(w2.tokensSpent).toBe(0);
    const v = await ledger.checkAndReserve(REPO, estimate("c", 900), CAPS, day2);
    expect(v.allowed).toBe(true);
    await ledger.close();
  });

  it("dedupes reservations by id (idempotent)", async () => {
    const ledger = createSqliteLedger();
    const now = new Date("2026-07-10T10:00:00Z");
    const e = estimate("dup", 100);
    await ledger.checkAndReserve(REPO, e, CAPS, now);
    await ledger.recordSpend({
      id: "dup",
      repo: REPO,
      runId: "x",
      provider: "mock",
      tokens: { input: 0, output: 0, total: 100 },
      dollars: 0,
      at: now.toISOString(),
    });
    const w = await ledger.getWindow(REPO, CAPS, now);
    expect(w.tokensSpent).toBe(100); // duplicate id ignored
    await ledger.close();
  });
});
