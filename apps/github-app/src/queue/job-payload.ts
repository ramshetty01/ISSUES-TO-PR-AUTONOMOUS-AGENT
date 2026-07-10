/**
 * Build the normalized Job payload (shared-types) from a filtered webhook
 * event. The Job is what the dispatcher + worker consume, so this is the
 * contract boundary between the app and the rest of the pipeline.
 */
import type { Job, TriggerKind, RepoRef } from "@itpr/shared-types";

export interface BuildJobInput {
  /** GitHub delivery id — becomes the Job id + dedup key. */
  deliveryId: string;
  repo: RepoRef;
  installationId: number;
  trigger: TriggerKind;
  issueNumber?: number;
  prNumber?: number;
  labels: string[];
  /** Head sha when known (PR events); the worker resolves it otherwise. */
  headSha?: string;
  /** Injected clock for deterministic tests. */
  now?: () => Date;
}

export function buildJob(input: BuildJobInput): Job {
  const createdAt = (input.now ?? (() => new Date()))().toISOString();
  const job: Job = {
    id: input.deliveryId,
    repo: input.repo,
    installationId: input.installationId,
    trigger: input.trigger,
    headSha: input.headSha ?? "",
    labels: input.labels,
    createdAt,
  };
  if (input.issueNumber !== undefined) job.issueNumber = input.issueNumber;
  if (input.prNumber !== undefined) job.prNumber = input.prNumber;
  return job;
}
