/** Validate + normalize a received message body into a well-formed Job. */
import type { Job } from "@itpr/shared-types";

export type NormalizeResult =
  | { ok: true; job: Job }
  | { ok: false; reason: string };

/** Runtime validation of the Job contract (defends against malformed messages). */
export function normalizeJob(raw: unknown): NormalizeResult {
  if (!raw || typeof raw !== "object") {
    return { ok: false, reason: "job is not an object" };
  }
  const j = raw as Record<string, unknown>;
  if (typeof j.id !== "string" || j.id.length === 0) {
    return { ok: false, reason: "missing job id" };
  }
  const repo = j.repo as Record<string, unknown> | undefined;
  if (!repo || typeof repo.owner !== "string" || typeof repo.name !== "string") {
    return { ok: false, reason: "missing repo owner/name" };
  }
  if (typeof j.installationId !== "number") {
    return { ok: false, reason: "missing installationId" };
  }
  if (j.trigger !== "issue_labeled" && j.trigger !== "pr_comment") {
    return { ok: false, reason: "invalid trigger" };
  }
  if (j.trigger === "issue_labeled" && typeof j.issueNumber !== "number") {
    return { ok: false, reason: "issue_labeled requires issueNumber" };
  }
  if (j.trigger === "pr_comment" && typeof j.prNumber !== "number") {
    return { ok: false, reason: "pr_comment requires prNumber" };
  }
  return { ok: true, job: raw as Job };
}
