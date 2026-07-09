/**
 * Narrowed GitHub webhook payloads the github-app actually consumes.
 * These are intentionally minimal projections of the full GitHub event shapes.
 */
import type { RepoRef } from "./repo.js";

/** Common fields present on every handled webhook event. */
export interface WebhookBase {
  /** X-GitHub-Delivery id, used for replay protection + dedup. */
  deliveryId: string;
  installationId: number;
  repo: RepoRef;
}

/** An actor (user or bot) that triggered an event. */
export interface Actor {
  login: string;
  type: "User" | "Bot" | "Organization";
}

/** issues.labeled — the primary trigger. */
export interface IssueLabeledEvent extends WebhookBase {
  event: "issue_labeled";
  issueNumber: number;
  label: string;
  labels: string[];
  actor: Actor;
}

/** issue_comment.created on a pull request — a command comment. */
export interface PrCommentEvent extends WebhookBase {
  event: "pr_comment";
  prNumber: number;
  body: string;
  actor: Actor;
}

/** installation created/deleted. */
export interface InstallationEvent extends WebhookBase {
  event: "installation";
  action: "created" | "deleted" | "suspend" | "unsuspend";
}

/** ping event sent by GitHub when a webhook is configured. */
export interface PingEvent {
  event: "ping";
  deliveryId: string;
  zen: string;
}

/** Discriminated union of all handled events. */
export type WebhookEvent =
  | IssueLabeledEvent
  | PrCommentEvent
  | InstallationEvent
  | PingEvent;
