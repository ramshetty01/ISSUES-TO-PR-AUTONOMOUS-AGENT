/**
 * Pre-run cost estimate for a job. Even $0 providers are metered in tokens, so
 * every job gets a token estimate; dollars are imputed at the provider's list
 * price (0 for local/free providers).
 */
import type { Job } from "@itpr/shared-types";

export interface CostEstimate {
  tokens: number;
  dollars: number;
}

export interface EstimatorOptions {
  /** Baseline tokens a run is expected to consume. */
  baseTokens?: number;
  /** Imputed dollars per 1k tokens for the selected provider (0 = free). */
  dollarsPer1kTokens?: number;
}

const DEFAULT_BASE_TOKENS = 20_000;

/**
 * Deterministic heuristic: a base budget, nudged up for pr_comment follow-ups
 * (extra context) — refined by the worker's real metering later.
 */
export function estimateJobCost(
  job: Job,
  opts: EstimatorOptions = {},
): CostEstimate {
  const base = opts.baseTokens ?? DEFAULT_BASE_TOKENS;
  const tokens = job.trigger === "pr_comment" ? Math.round(base * 1.25) : base;
  const dollars = ((opts.dollarsPer1kTokens ?? 0) * tokens) / 1000;
  return { tokens, dollars };
}
