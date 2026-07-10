/**
 * Ledger interface + shared budget arithmetic. Concrete backends
 * (dynamodb-ledger, sqlite-ledger) implement only persistence primitives;
 * window aggregation, reservation, and verdicts live here so both behave
 * identically.
 */
import type {
  RepoRef,
  LedgerEntry,
  BudgetWindow,
  BudgetVerdict,
} from "@itpr/shared-types";
import { dailyWindow } from "./daily-window.js";
import type { BudgetCaps } from "./repo-budget.js";
import { BudgetExceeded } from "./errors.js";

/** A pre-run cost estimate to check + reserve. */
export interface SpendEstimate {
  tokens: number;
  dollars: number;
  runId: string;
  provider: string;
  /** Idempotency id for the reservation entry. */
  id: string;
}

export interface Ledger {
  recordSpend(entry: LedgerEntry): Promise<void>;
  getWindow(repo: RepoRef, caps: BudgetCaps, now?: Date): Promise<BudgetWindow>;
  checkAndReserve(
    repo: RepoRef,
    estimate: SpendEstimate,
    caps: BudgetCaps,
    now?: Date,
  ): Promise<BudgetVerdict>;
  close(): Promise<void>;
}

/** Persistence primitives a backend must provide. */
export interface LedgerStore {
  /** Append an entry (must be atomic w.r.t. the sum used by checkAndReserve). */
  append(entry: LedgerEntry): Promise<void>;
  /** Sum tokens + dollars for a repo within [start, end). */
  sum(
    repo: RepoRef,
    start: string,
    end: string,
  ): Promise<{ tokens: number; dollars: number }>;
  /** Atomically sum-then-append when the reservation fits; returns the pre-spend totals. */
  reserve(
    repo: RepoRef,
    start: string,
    end: string,
    caps: BudgetCaps,
    entry: LedgerEntry,
  ): Promise<{ ok: boolean; tokens: number; dollars: number }>;
  close(): Promise<void>;
}

/** Base Ledger implemented in terms of a LedgerStore. */
export class BaseLedger implements Ledger {
  constructor(private readonly store: LedgerStore) {}

  async recordSpend(entry: LedgerEntry): Promise<void> {
    await this.store.append(entry);
  }

  async getWindow(
    repo: RepoRef,
    caps: BudgetCaps,
    now: Date = new Date(),
  ): Promise<BudgetWindow> {
    const w = dailyWindow(now);
    const spent = await this.store.sum(repo, w.start, w.end);
    return {
      repo,
      periodStart: w.start,
      periodEnd: w.end,
      tokenCap: caps.tokenCap,
      dollarCap: caps.dollarCap,
      tokensSpent: spent.tokens,
      dollarsSpent: spent.dollars,
    };
  }

  async checkAndReserve(
    repo: RepoRef,
    estimate: SpendEstimate,
    caps: BudgetCaps,
    now: Date = new Date(),
  ): Promise<BudgetVerdict> {
    const w = dailyWindow(now);
    const entry: LedgerEntry = {
      id: estimate.id,
      repo,
      runId: estimate.runId,
      provider: estimate.provider,
      tokens: { input: 0, output: 0, total: estimate.tokens },
      dollars: estimate.dollars,
      at: now.toISOString(),
    };
    const res = await this.store.reserve(repo, w.start, w.end, caps, entry);
    const remainingTokens =
      caps.tokenCap > 0 ? Math.max(0, caps.tokenCap - res.tokens) : Infinity;
    const remainingDollars =
      caps.dollarCap > 0 ? Math.max(0, caps.dollarCap - res.dollars) : Infinity;

    if (!res.ok) {
      const overTokens =
        caps.tokenCap > 0 && res.tokens + estimate.tokens > caps.tokenCap;
      return {
        allowed: false,
        reason: overTokens
          ? "daily token cap reached"
          : "daily dollar cap reached",
        remainingTokens,
        remainingDollars,
      };
    }
    return {
      allowed: true,
      remainingTokens: Math.max(
        0,
        remainingTokens === Infinity
          ? Infinity
          : remainingTokens - estimate.tokens,
      ),
      remainingDollars: Math.max(
        0,
        remainingDollars === Infinity
          ? Infinity
          : remainingDollars - estimate.dollars,
      ),
    };
  }

  async close(): Promise<void> {
    await this.store.close();
  }
}

/** Pure helper: would this estimate fit under the caps given prior spend? */
export function fits(
  caps: BudgetCaps,
  spent: { tokens: number; dollars: number },
  estimate: { tokens: number; dollars: number },
): boolean {
  if (caps.tokenCap > 0 && spent.tokens + estimate.tokens > caps.tokenCap) {
    return false;
  }
  if (caps.dollarCap > 0 && spent.dollars + estimate.dollars > caps.dollarCap) {
    return false;
  }
  return true;
}

export { BudgetExceeded };
