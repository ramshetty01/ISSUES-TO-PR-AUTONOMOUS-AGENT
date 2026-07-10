/**
 * Webhook route: verify → parse the GitHub payload into a narrowed event →
 * dispatch to the matching handler. Returns the verifier's status on failure,
 * 202 with the handler result on success.
 */
import express, { Router, type Request } from "express";
import type {
  IssueLabeledEvent,
  PrCommentEvent,
  InstallationEvent,
  Actor,
  RepoRef,
} from "@itpr/shared-types";
import type { WebhookVerifier } from "../github/webhook-verifier.js";
import {
  handleIssueLabeled,
  type HandlerDeps,
  type HandlerResult,
} from "../handlers/issue-labeled.handler.js";
import { handlePrComment } from "../handlers/pr-comment.handler.js";
import { handleInstallation } from "../handlers/installation.handler.js";
import { handlePing } from "../handlers/ping.handler.js";
import { logger } from "../logging/logger.js";

export interface WebhookDeps {
  verifier: WebhookVerifier;
  handlerDeps: HandlerDeps;
}

interface RawBodyRequest extends Request {
  rawBody?: Buffer;
}

// --- payload parsing (narrow the raw GitHub JSON to our event types) ---------

interface RawPayload {
  action?: string;
  installation?: { id?: number };
  repository?: { name?: string; owner?: { login?: string } };
  sender?: { login?: string; type?: string };
  issue?: { number?: number; labels?: Array<{ name?: string }>; pull_request?: unknown };
  label?: { name?: string };
  comment?: { body?: string };
}

function repoOf(p: RawPayload): RepoRef {
  return { owner: p.repository?.owner?.login ?? "", name: p.repository?.name ?? "" };
}

function actorOf(p: RawPayload): Actor {
  const type = p.sender?.type;
  return {
    login: p.sender?.login ?? "",
    type: type === "Bot" || type === "Organization" ? type : "User",
  };
}

export function parseIssueLabeled(
  deliveryId: string,
  p: RawPayload,
): IssueLabeledEvent | undefined {
  if (p.action !== "labeled" || !p.issue) return undefined;
  return {
    event: "issue_labeled",
    deliveryId,
    installationId: p.installation?.id ?? 0,
    repo: repoOf(p),
    issueNumber: p.issue.number ?? 0,
    label: p.label?.name ?? "",
    labels: (p.issue.labels ?? []).map((l) => l.name ?? ""),
    actor: actorOf(p),
  };
}

export function parsePrComment(
  deliveryId: string,
  p: RawPayload,
): PrCommentEvent | undefined {
  if (p.action !== "created" || !p.issue?.pull_request) return undefined;
  return {
    event: "pr_comment",
    deliveryId,
    installationId: p.installation?.id ?? 0,
    repo: repoOf(p),
    prNumber: p.issue.number ?? 0,
    body: p.comment?.body ?? "",
    actor: actorOf(p),
  };
}

function parseInstallation(
  deliveryId: string,
  p: RawPayload,
): InstallationEvent {
  const action = p.action;
  return {
    event: "installation",
    deliveryId,
    installationId: p.installation?.id ?? 0,
    repo: repoOf(p),
    action:
      action === "deleted" || action === "suspend" || action === "unsuspend"
        ? action
        : "created",
  };
}

/** Route a verified payload to a handler. Exported for direct testing. */
export async function dispatchEvent(
  ghEvent: string,
  deliveryId: string,
  payload: RawPayload,
  deps: HandlerDeps,
): Promise<HandlerResult> {
  switch (ghEvent) {
    case "issues": {
      const ev = parseIssueLabeled(deliveryId, payload);
      return ev
        ? handleIssueLabeled(ev, deps)
        : { action: "skipped", reason: "unhandled issues action" };
    }
    case "issue_comment": {
      const ev = parsePrComment(deliveryId, payload);
      return ev
        ? handlePrComment(ev, deps)
        : { action: "skipped", reason: "comment not on a PR" };
    }
    case "installation":
      return handleInstallation(parseInstallation(deliveryId, payload));
    case "ping":
      return handlePing();
    default:
      return { action: "skipped", reason: `unhandled event: ${ghEvent}` };
  }
}

/** Express router mounting POST /webhook with raw-body capture + verification. */
export function createWebhookRouter(deps: WebhookDeps): Router {
  const router = Router();
  router.use(
    express.json({
      verify: (req, _res, buf) => {
        (req as RawBodyRequest).rawBody = Buffer.from(buf);
      },
    }),
  );

  router.post("/webhook", async (req, res) => {
    const rawBody = (req as RawBodyRequest).rawBody ?? Buffer.alloc(0);
    const signature = req.header("x-hub-signature-256");
    const deliveryId = req.header("x-github-delivery");
    const ghEvent = req.header("x-github-event") ?? "unknown";

    const outcome = deps.verifier.verify({
      rawBody,
      parsed: req.body,
      signature,
      deliveryId,
    });
    if (!outcome.ok) {
      return res.status(outcome.status).json({ error: outcome.reason });
    }

    try {
      const result = await dispatchEvent(
        ghEvent,
        deliveryId!,
        outcome.payload as RawPayload,
        deps.handlerDeps,
      );
      return res.status(202).json(result);
    } catch (err) {
      logger.error("handler failed", { error: String(err), event: ghEvent });
      return res.status(500).json({ error: "handler failed" });
    }
  });

  return router;
}
