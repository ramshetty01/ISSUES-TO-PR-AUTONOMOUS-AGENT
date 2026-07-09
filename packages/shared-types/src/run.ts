/**
 * Run lifecycle, timeline, and summary types. Consumed by the dashboard and
 * the worker's run-summary output.
 */
import type { Job } from "./job.js";
import type { TokenUsage } from "./budget.js";
import type { Refusal, SafetyEvent } from "./safety.js";

/** Lifecycle state of a run. */
export type RunState =
  | "queued"
  | "dispatched"
  | "running"
  | "succeeded"
  | "failed"
  | "refused";

/** A single event on the run timeline. */
export interface TimelineEvent {
  /** ISO-8601 timestamp. */
  at: string;
  /** Short machine-readable event kind (e.g. "plan", "edit", "test", "pr_opened"). */
  kind: string;
  message: string;
  /** Optional structured payload. */
  data?: Record<string, unknown>;
}

/** Terminal (or in-progress) summary of a run, emitted by the worker. */
export interface RunSummary {
  runId: string;
  job: Job;
  state: RunState;
  timeline: TimelineEvent[];
  usage: TokenUsage;
  /** Imputed dollar cost at list price. */
  dollars: number;
  safetyEvents: SafetyEvent[];
  /** Populated when state === "refused". */
  refusal?: Refusal;
  /** URL of the opened PR, when successful. */
  prUrl?: string;
  /** Link into the self-hosted Langfuse trace. */
  traceUrl?: string;
  /** ISO-8601 timestamps. */
  startedAt: string;
  finishedAt?: string;
}
