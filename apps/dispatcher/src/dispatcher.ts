/**
 * Orchestrate a single received message: normalize → budget check → repo-policy
 * gate → spawn worker → ack/nack/DLQ. Every decision is audited + metered.
 */
import type { Job, BudgetVerdict } from "@itpr/shared-types";
import type { ReceivedJob } from "./queue/sqs-client.js";
import { normalizeJob } from "./job-normalizer.js";
import { AuditLog } from "./observability/audit-log.js";
import { Metrics } from "./observability/metrics.js";
import { startSpan } from "./observability/traces.js";

export interface RepoPolicyResult {
  ok: boolean;
  reason?: string;
}

export interface WorkerOutcome {
  exitCode: number;
  timedOut: boolean;
}

/** Injected collaborators (all mockable). */
export interface DispatcherDeps {
  checkBudget: (job: Job) => Promise<BudgetVerdict>;
  checkRepoPolicy: (job: Job) => Promise<RepoPolicyResult>;
  runWorker: (job: Job) => Promise<WorkerOutcome>;
  ack: (received: ReceivedJob) => Promise<void>;
  nack: (received: ReceivedJob) => Promise<void>;
  deadLetter: (received: ReceivedJob, reason: string) => Promise<void>;
  maxReceives: number;
  audit: AuditLog;
  metrics: Metrics;
}

export type DispatchResult =
  | "dispatched"
  | "refused"
  | "failed"
  | "dead_lettered"
  | "malformed";

export class Dispatcher {
  constructor(private readonly deps: DispatcherDeps) {}

  async handle(received: ReceivedJob): Promise<DispatchResult> {
    const d = this.deps;
    d.metrics.inc("received");

    // Poison-message guard first.
    if (received.receiveCount > d.maxReceives) {
      await d.deadLetter(received, "max receives exceeded");
      d.metrics.inc("dead_lettered");
      d.audit.record(received.job.id, "dead_lettered", "max receives exceeded");
      return "dead_lettered";
    }

    const norm = normalizeJob(received.job);
    if (!norm.ok) {
      await d.deadLetter(received, norm.reason);
      d.metrics.inc("malformed");
      d.audit.record(received.job.id ?? "unknown", "malformed", norm.reason);
      return "malformed";
    }
    const job = norm.job;

    // Budget gate.
    const verdict = await d.checkBudget(job);
    if (!verdict.allowed) {
      await d.ack(received); // refusals are terminal — do not retry
      d.metrics.inc("refused");
      d.audit.record(job.id, "refused", verdict.reason ?? "over budget");
      return "refused";
    }

    // Repo-policy gate.
    const policy = await d.checkRepoPolicy(job);
    if (!policy.ok) {
      await d.ack(received);
      d.metrics.inc("refused");
      d.audit.record(job.id, "refused", policy.reason ?? "repo policy");
      return "refused";
    }

    // Spawn the worker.
    const span = startSpan("run_worker", { jobId: job.id });
    try {
      const outcome = await d.runWorker(job);
      if (outcome.exitCode === 0 && !outcome.timedOut) {
        await d.ack(received);
        span.end("ok");
        d.metrics.inc("dispatched");
        d.metrics.inc("succeeded");
        d.audit.record(job.id, "succeeded");
        return "dispatched";
      }
      // Non-zero / timeout: transient — return for redelivery.
      await d.nack(received);
      span.end("error", { exitCode: outcome.exitCode, timedOut: outcome.timedOut });
      d.metrics.inc("failed");
      d.audit.record(job.id, "failed", outcome.timedOut ? "timeout" : `exit ${outcome.exitCode}`);
      return "failed";
    } catch (err) {
      await d.nack(received);
      span.end("error", { error: String(err) });
      d.metrics.inc("failed");
      d.audit.record(job.id, "failed", String(err));
      return "failed";
    }
  }
}
