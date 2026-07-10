/**
 * Handle an issue_comment.created on a pull request: if the comment is a
 * command from a permitted actor on an allowlisted repo, enqueue a Job.
 */
import type { PrCommentEvent } from "@itpr/shared-types";
import { isAllowedRepo } from "../filters/repo-allowlist.js";
import { isAllowedActor } from "../filters/actor-filter.js";
import { buildJob } from "../queue/job-payload.js";
import { logger } from "../logging/logger.js";
import {
  permissionGate,
  tryAck,
  type HandlerDeps,
  type HandlerResult,
} from "./issue-labeled.handler.js";

const DEFAULT_COMMAND = "/agent";

/** True if the comment body contains the trigger command as a whole word. */
export function hasCommand(body: string, command: string): boolean {
  const re = new RegExp(`(^|\\s)${escapeRegExp(command)}(\\s|$)`);
  return re.test(body);
}

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export async function handlePrComment(
  event: PrCommentEvent,
  deps: HandlerDeps,
): Promise<HandlerResult> {
  const command = deps.filters.command ?? DEFAULT_COMMAND;
  if (!isAllowedActor(event.actor, deps.filters.actorPolicy)) {
    return { action: "skipped", reason: "actor not permitted" };
  }
  if (!isAllowedRepo(event.repo, deps.filters.allowlist)) {
    return { action: "skipped", reason: "repo not allowlisted" };
  }
  if (!hasCommand(event.body, command)) {
    return { action: "skipped", reason: "no command in comment" };
  }

  const job = buildJob({
    deliveryId: event.deliveryId,
    repo: event.repo,
    installationId: event.installationId,
    trigger: "pr_comment",
    prNumber: event.prNumber,
    labels: [],
    ...(deps.now ? { now: deps.now } : {}),
  });
  const denied = await permissionGate(job, deps);
  if (denied) return denied;

  const messageId = await deps.enqueuer.enqueue(job);
  logger.info("pr comment enqueued", { jobId: job.id, messageId });
  await tryAck(job, "On it — the agent is working on this request.", deps);
  return { action: "enqueued", jobId: job.id, messageId };
}
