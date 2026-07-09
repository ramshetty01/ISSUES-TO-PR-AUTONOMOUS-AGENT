/**
 * Safety refusal + event types. Mirrors the worker safety layer
 * (worker/src/issue_to_pr_agent/safety/). Rubric-critical.
 */

/** Why the agent refused to act or blocked an operation. */
export type RefusalReason =
  | "budget_exceeded"
  | "branch_protection_missing"
  | "forbidden_path"
  | "workflow_write_blocked"
  | "force_push_blocked"
  | "secret_detected"
  | "pii_detected"
  | "command_denied"
  | "path_jail_escape"
  | "diff_too_large"
  | "installation_permissions_missing";

/** A structured refusal surfaced to the user and the audit log. */
export interface Refusal {
  reason: RefusalReason;
  /** Human-readable explanation. */
  message: string;
  /** Optional offending path/command/detail. */
  detail?: string;
}

/** A safety-relevant event recorded during a run. */
export interface SafetyEvent {
  /** ISO-8601 timestamp. */
  at: string;
  reason: RefusalReason;
  message: string;
  path?: string;
}

/** Result of checking a command/path against a denylist. */
export interface DenylistVerdict {
  blocked: boolean;
  /** The pattern that matched, when blocked. */
  matched?: string;
}
