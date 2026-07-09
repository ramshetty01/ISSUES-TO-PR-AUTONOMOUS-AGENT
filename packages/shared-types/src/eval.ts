/**
 * Eval harness types: seeded issues, per-issue results, and the aggregate
 * scorecard. Consumed by eval/runners and eval/metrics.
 */

/** Language/stack of a seeded issue and its fixture repo. */
export type EvalStack = "python" | "node" | "go" | "rust" | "java" | "mixed";

/** One seeded issue in the eval corpus. */
export interface SeededIssue {
  id: string;
  stack: EvalStack;
  /** Path to the issue markdown under eval/seeded-issues. */
  path: string;
  title: string;
  /** Fixture repo the issue targets (owner/name of a public repo). */
  fixtureRepo: string;
}

/** Metric scores for a single run, each normalized to [0, 1]. */
export interface EvalMetrics {
  passRate: number;
  prQuality: number;
  diffSize: number;
  coverageDelta: number;
  styleConformance: number;
  safetyScore: number;
  operatorUxScore: number;
}

/** Cost/latency captured for a single eval run. */
export interface EvalCost {
  tokens: number;
  /** Imputed dollars at list price. */
  dollars: number;
  wallClockSeconds: number;
  provider: string;
}

/** Result of running the agent against one seeded issue. */
export interface EvalResult {
  issueId: string;
  passed: boolean;
  metrics: EvalMetrics;
  cost: EvalCost;
  /** URL of the produced PR, if any. */
  prUrl?: string;
}

/** Aggregate scorecard across an eval run. */
export interface Scorecard {
  total: number;
  passed: number;
  passRate: number;
  metrics: EvalMetrics;
  cost: EvalCost;
  /** ISO-8601 timestamp of the run. */
  generatedAt: string;
}
