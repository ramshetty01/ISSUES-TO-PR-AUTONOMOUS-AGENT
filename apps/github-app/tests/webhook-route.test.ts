import { describe, it, expect, vi } from "vitest";
import express from "express";
import request from "supertest";
import { createWebhookRouter, dispatchEvent } from "../src/routes/webhook.js";
import { WebhookVerifier } from "../src/github/webhook-verifier.js";
import { computeSignature } from "../src/security/signature-check.js";
import type { HandlerDeps } from "../src/handlers/issue-labeled.handler.js";

const SECRET = "whsec_test";

function issuesLabeledPayload() {
  return {
    action: "labeled",
    installation: { id: 42 },
    repository: { name: "widgets", owner: { login: "acme" } },
    sender: { login: "alice", type: "User" },
    label: { name: "agent-fix" },
    issue: {
      number: 7,
      title: "Fix duration formatting",
      body: "Never render 60s.",
      labels: [{ name: "agent-fix" }],
    },
  };
}

function mkDeps(): { deps: HandlerDeps; enqueue: ReturnType<typeof vi.fn> } {
  const enqueue = vi.fn().mockResolvedValue("m-1");
  return {
    enqueue,
    deps: {
      enqueuer: { enqueue },
      filters: {
        allowedLabels: ["agent-fix"],
        allowlist: [{ owner: "acme", name: "widgets" }],
      },
    },
  };
}

function mkApp(deps: HandlerDeps) {
  const app = express();
  app.use(
    createWebhookRouter({
      verifier: new WebhookVerifier({ secret: SECRET }),
      handlerDeps: deps,
    }),
  );
  return app;
}

describe("dispatchEvent", () => {
  it("routes a ping to pong", async () => {
    const { deps } = mkDeps();
    expect(await dispatchEvent("ping", "d", {}, deps)).toEqual({ action: "pong" });
  });

  it("skips unhandled events", async () => {
    const { deps } = mkDeps();
    const res = await dispatchEvent("push", "d", {}, deps);
    expect(res).toMatchObject({ action: "skipped" });
  });
});

describe("POST /webhook (end-to-end)", () => {
  it("verifies + dispatches a labeled issue into one enqueued job", async () => {
    const { deps, enqueue } = mkDeps();
    const app = mkApp(deps);
    const body = JSON.stringify(issuesLabeledPayload());

    const res = await request(app)
      .post("/webhook")
      .set("content-type", "application/json")
      .set("x-github-event", "issues")
      .set("x-github-delivery", "delivery-1")
      .set("x-hub-signature-256", computeSignature(SECRET, body))
      .send(body);

    expect(res.status).toBe(202);
    expect(res.body).toMatchObject({ action: "enqueued", jobId: "delivery-1" });
    expect(enqueue).toHaveBeenCalledOnce();
  });

  it("rejects a bad signature with 401 and does not enqueue", async () => {
    const { deps, enqueue } = mkDeps();
    const app = mkApp(deps);
    const body = JSON.stringify(issuesLabeledPayload());

    const res = await request(app)
      .post("/webhook")
      .set("content-type", "application/json")
      .set("x-github-event", "issues")
      .set("x-github-delivery", "delivery-2")
      .set("x-hub-signature-256", "sha256=bad")
      .send(body);

    expect(res.status).toBe(401);
    expect(enqueue).not.toHaveBeenCalled();
  });
});
