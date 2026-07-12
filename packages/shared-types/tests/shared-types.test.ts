import { describe, it, expectTypeOf } from "vitest";
import type {
  Job,
  RepoRef,
  BudgetVerdict,
  RunSummary,
  RunState,
  WebhookEvent,
  IssueLabeledEvent,
  Refusal,
  RefusalReason,
  Scorecard,
} from "../src/index.js";

describe("@itpr/shared-types", () => {
  it("Job carries repo, trigger, and head sha", () => {
    const job: Job = {
      id: "d-1",
      repo: { owner: "acme", name: "widgets" },
      installationId: 42,
      trigger: "issue_labeled",
      issueNumber: 7,
      headSha: "abc123",
      labels: ["agent-fix"],
      createdAt: "2026-07-09T00:00:00Z",
    };
    expectTypeOf(job.repo).toEqualTypeOf<RepoRef>();
    expectTypeOf(job.trigger).toEqualTypeOf<"issue_labeled" | "pr_comment">();
  });

  it("RunState is a closed union", () => {
    expectTypeOf<RunState>().toEqualTypeOf<
      "queued" | "dispatched" | "running" | "succeeded" | "failed" | "refused"
    >();
  });

  it("BudgetVerdict exposes remaining budget", () => {
    const verdict: BudgetVerdict = {
      allowed: false,
      reason: "daily token cap reached",
      remainingTokens: 0,
      remainingDollars: 0,
    };
    expectTypeOf(verdict.allowed).toBeBoolean();
  });

  it("WebhookEvent discriminates by event tag", () => {
    const ev: WebhookEvent = {
      event: "issue_labeled",
      deliveryId: "x",
      installationId: 1,
      repo: { owner: "a", name: "b" },
      issueNumber: 1,
      issueTitle: "Fix a bug",
      issueBody: "Detailed reproduction",
      label: "agent-fix",
      labels: ["agent-fix"],
      actor: { login: "u", type: "User" },
    };
    if (ev.event === "issue_labeled") {
      expectTypeOf(ev).toEqualTypeOf<IssueLabeledEvent>();
    }
  });

  it("Refusal reason is constrained", () => {
    const r: Refusal = { reason: "secret_detected", message: "token found" };
    expectTypeOf(r.reason).toEqualTypeOf<RefusalReason>();
  });

  it("RunSummary and Scorecard are exported", () => {
    expectTypeOf<RunSummary>().toHaveProperty("timeline");
    expectTypeOf<Scorecard>().toHaveProperty("passRate");
  });
});
