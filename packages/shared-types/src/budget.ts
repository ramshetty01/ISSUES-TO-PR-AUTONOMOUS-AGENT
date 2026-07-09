/**
 * Token/dollar budget types. Free-tier providers meter tokens, so budgets are
 * enforced even at $0. Backed by the budget-ledger package.
 */
import type { RepoRef } from "./repo.js";

/** Token counts for a single call or an aggregate. */
export interface TokenUsage {
  input: number;
  output: number;
  total: number;
}

/** A rolling budget window (typically daily) for one repo. */
export interface BudgetWindow {
  repo: RepoRef;
  /** ISO-8601 start of the window. */
  periodStart: string;
  /** ISO-8601 end of the window. */
  periodEnd: string;
  tokenCap: number;
  dollarCap: number;
  tokensSpent: number;
  dollarsSpent: number;
}

/** An append-only ledger entry recording spend from one run. */
export interface LedgerEntry {
  id: string;
  repo: RepoRef;
  runId: string;
  provider: string;
  tokens: TokenUsage;
  /** Dollars imputed at list price ($0 providers still record tokens). */
  dollars: number;
  /** ISO-8601 timestamp. */
  at: string;
}

/** Result of a budget check. */
export interface BudgetVerdict {
  allowed: boolean;
  /** Populated when allowed === false. */
  reason?: string;
  remainingTokens: number;
  remainingDollars: number;
}
