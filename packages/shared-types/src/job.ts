/**
 * The Job payload produced by github-app, enqueued to SQS, and consumed by the
 * dispatcher + worker. This TypeScript contract must stay in sync with the
 * worker's pydantic Job model (worker/src/issue_to_pr_agent/job.py).
 */
import type { RepoRef } from "./repo.js";

/** What kind of event triggered the job. */
export type TriggerKind = "issue_labeled" | "pr_comment";

/** A unit of work: fix an issue (or act on a PR comment) in a repo. */
export interface Job {
  /** Stable id; also used as the SQS dedup key (GitHub delivery id). */
  id: string;
  repo: RepoRef;
  /** GitHub App installation id used to mint a scoped token. */
  installationId: number;
  trigger: TriggerKind;
  /** Set when trigger === "issue_labeled". */
  issueNumber?: number;
  /** Issue content captured from the webhook for deterministic worker prompts. */
  issueTitle?: string;
  issueBody?: string;
  /** Set when trigger === "pr_comment". */
  prNumber?: number;
  /** Head commit sha the worker should base its work on. */
  headSha: string;
  /** Labels present on the issue/PR at trigger time. */
  labels: string[];
  /** ISO-8601 creation timestamp. */
  createdAt: string;
}
