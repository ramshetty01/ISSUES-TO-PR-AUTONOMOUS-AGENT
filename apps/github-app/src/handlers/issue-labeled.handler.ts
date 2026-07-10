/**
 * Handle an issues.labeled event: apply filters, then build + enqueue a Job.
 */
import type { IssueLabeledEvent, AllowlistEntry } from "@itpr/shared-types";
import { matchesTriggerLabel } from "../filters/label-filter.js";
import { isAllowedRepo } from "../filters/repo-allowlist.js";
import { isAllowedActor, type ActorPolicy } from "../filters/actor-filter.js";
import { buildJob } from "../queue/job-payload.js";
import { logger } from "../logging/logger.js";

/** Anything that can enqueue a Job (JobEnqueuer or a mock). */
export interface Enqueuer {
  enqueue: (job: import("@itpr/shared-types").Job) => Promise<string>;
}

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
    labels: event.labels,
    ...(deps.now ? { now: deps.now } : {}),
  });
  const messageId = await deps.enqueuer.enqueue(job);
  logger.info("issue enqueued", { jobId: job.id, messageId });
  return { action: "enqueued", jobId: job.id, messageId };
}
