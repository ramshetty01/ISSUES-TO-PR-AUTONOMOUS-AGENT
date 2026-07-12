/**
 * Handle an issues.labeled event: apply filters, then build + enqueue a Job.
 */
import type { IssueLabeledEvent, AllowlistEntry, Job } from "@itpr/shared-types";
import { matchesTriggerLabel } from "../filters/label-filter.js";
import { isAllowedRepo } from "../filters/repo-allowlist.js";
import { isAllowedActor, type ActorPolicy } from "../filters/actor-filter.js";
import { buildJob } from "../queue/job-payload.js";
import { logger } from "../logging/logger.js";

/** Anything that can enqueue a Job (JobEnqueuer or a mock). */
export interface Enqueuer {
  enqueue: (job: Job) => Promise<string>;
}

/** Verifies the installation has the scopes the agent needs. */
export type PermissionChecker = (
  job: Job,
) => Promise<{ ok: boolean; missing?: string[] }>;

/** Posts an acknowledgement on the triggering issue/PR (best-effort). */
export type Acker = (args: {
  job: Job;
  message: string;
}) => Promise<void>;

export interface FilterConfig {
  allowedLabels: string[];
  allowlist: AllowlistEntry[];
  actorPolicy?: ActorPolicy;
  /** Command that triggers on a PR comment. Default /agent. */
  command?: string;
}

export interface HandlerDeps {
  enqueuer: Enqueuer;
  filters: FilterConfig;
  now?: () => Date;
  /** Optional installation permission gate. */
  checkPermissions?: PermissionChecker;
  /** Optional ack poster; failures are logged, not fatal. */
  ack?: Acker;
}

/** Run the optional permission gate; returns a skip result if it fails. */
export async function permissionGate(
  job: Job,
  deps: HandlerDeps,
): Promise<HandlerResult | undefined> {
  if (!deps.checkPermissions) return undefined;
  const res = await deps.checkPermissions(job);
  if (!res.ok) {
    return {
      action: "skipped",
      reason: `missing permissions: ${(res.missing ?? []).join(", ")}`,
    };
  }
  return undefined;
}

/** Post an ack, swallowing errors (never block enqueue on a failed comment). */
export async function tryAck(job: Job, message: string, deps: HandlerDeps): Promise<void> {
  if (!deps.ack) return;
  try {
    await deps.ack({ job, message });
  } catch (err) {
    logger.warn("ack failed", { jobId: job.id, error: String(err) });
  }
}

export type HandlerResult =
  | { action: "enqueued"; jobId: string; messageId: string }
  | { action: "skipped"; reason: string }
  | { action: "recorded"; detail: string }
  | { action: "pong" };

export async function handleIssueLabeled(
  event: IssueLabeledEvent,
  deps: HandlerDeps,
): Promise<HandlerResult> {
  if (!isAllowedActor(event.actor, deps.filters.actorPolicy)) {
    return { action: "skipped", reason: "actor not permitted" };
  }
  if (!isAllowedRepo(event.repo, deps.filters.allowlist)) {
    return { action: "skipped", reason: "repo not allowlisted" };
  }
  if (!matchesTriggerLabel(event.labels, deps.filters.allowedLabels)) {
    return { action: "skipped", reason: "no trigger label" };
  }

  const job = buildJob({
    deliveryId: event.deliveryId,
    repo: event.repo,
    installationId: event.installationId,
    trigger: "issue_labeled",
    issueNumber: event.issueNumber,
    issueTitle: event.issueTitle,
    issueBody: event.issueBody,
    labels: event.labels,
    ...(deps.now ? { now: deps.now } : {}),
  });

  const denied = await permissionGate(job, deps);
  if (denied) return denied;

  const messageId = await deps.enqueuer.enqueue(job);
  logger.info("issue enqueued", { jobId: job.id, messageId });
  await tryAck(job, "On it — the agent is working on this issue.", deps);
  return { action: "enqueued", jobId: job.id, messageId };
}
