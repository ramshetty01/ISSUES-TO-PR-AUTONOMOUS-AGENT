import { describe, it, expect } from "vitest";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { createSqliteLedger } from "@itpr/budget-ledger";
import type { Job } from "@itpr/shared-types";
import { BudgetService } from "../src/budget/budget-service.js";
import { estimateJobCost } from "../src/budget/cost-estimator.js";
import { loadBudgetDefaults, FALLBACK_DEFAULTS } from "../src/budget/budget-policy.js";

const here = dirname(fileURLToPath(import.meta.url));
const POLICY = resolve(here, "../../../policies/budget-defaults.yaml");

const job = (id: string, trigger: Job["trigger"] = "issue_labeled"): Job => ({
  id,
  repo: { owner: "acme", name: "widgets" },
  installationId: 42,
  trigger,
  issueNumber: 7,
  headSha: "",
  labels: ["agent-fix"],
  createdAt: "2026-07-10T12:00:00.000Z",
});

describe("cost-estimator", () => {
  it("meters tokens even at $0", () => {
    const est = estimateJobCost(job("a"));
    expect(est.tokens).toBeGreaterThan(0);
    expect(est.dollars).toBe(0);
  });

  it("estimates more for pr_comment and imputes dollars at a price", () => {
    const issue = estimateJobCost(job("a", "issue_labeled"), { baseTokens: 1000 });
    const pr = estimateJobCost(job("b", "pr_comment"), {
      baseTokens: 1000,
      dollarsPer1kTokens: 2,
    });
    expect(pr.tokens).toBeGreaterThan(issue.tokens);
    expect(pr.dollars).toBeCloseTo((2 * 1250) / 1000);
  });
});

describe("budget-policy", () => {
  it("loads defaults from the policy YAML", () => {
    const d = loadBudgetDefaults(POLICY);
    expect(d.tokenCap).toBeGreaterThan(0);
    expect(d.dollarCap).toBeGreaterThan(0);
  });
});

describe("BudgetService", () => {
  const now = () => new Date("2026-07-10T12:00:00Z");

  it("reserves a job under cap", async () => {
    const svc = new BudgetService({
      ledger: createSqliteLedger(),
      defaults: { tokenCap: 100_000, dollarCap: 5 },
      estimator: { baseTokens: 20_000 },
      now,
    });
    const v = await svc.checkAndReserve(job("a"));
    expect(v.allowed).toBe(true);
  });

  it("refuses a job that exceeds the token cap and does not reserve it", async () => {
    const ledger = createSqliteLedger();
    const svc = new BudgetService({
      ledger,
      defaults: { tokenCap: 25_000, dollarCap: 5 },
      estimator: { baseTokens: 20_000 },
      now,
    });
    // first reservation (20k) fits
    expect((await svc.checkAndReserve(job("a"))).allowed).toBe(true);
    // second (another 20k -> 40k > 25k) refused
    const v2 = await svc.checkAndReserve(job("b"));
    expect(v2.allowed).toBe(false);
    expect(v2.reason).toContain("token");
    await ledger.close();
  });

  it("uses FALLBACK_DEFAULTS shape when needed", () => {
    expect(FALLBACK_DEFAULTS.tokenCap).toBeGreaterThan(0);
  });
});
