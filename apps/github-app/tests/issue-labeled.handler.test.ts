import { describe, it, expect, vi } from "vitest";
import type { IssueLabeledEvent } from "@itpr/shared-types";
import {
  handleIssueLabeled,
  type HandlerDeps,
} from "../src/handlers/issue-labeled.handler.js";

const baseEvent: IssueLabeledEvent = {
  event: "issue_labeled",
  deliveryId: "d-1",
  installationId: 42,
  repo: { owner: "acme", name: "widgets" },
  issueNumber: 7,
  label: "agent-fix",
  labels: ["bug", "agent-fix"],
  actor: { login: "alice", type: "User" },
};

function deps(overrides: Partial<HandlerDeps["filters"]> = {}): {
  deps: HandlerDeps;
  enqueue: ReturnType<typeof vi.fn>;
} {
  const enqueue = vi.fn().mockResolvedValue("m-1");
  return {
    enqueue,
    deps: {
      enqueuer: { enqueue },
      filters: {
        allowedLabels: ["agent-fix"],
        allowlist: [{ owner: "acme", name: "widgets" }],
        ...overrides,
      },
      now: () => new Date("2026-07-10T12:00:00Z"),
    },
  };
}

describe("handleIssueLabeled", () => {
  it("enqueues when actor, repo, and label all pass", async () => {
    const { deps: d, enqueue } = deps();
    const res = await handleIssueLabeled(baseEvent, d);
    expect(res).toEqual({ action: "enqueued", jobId: "d-1", messageId: "m-1" });
    const job = enqueue.mock.calls[0]![0];
    expect(job.trigger).toBe("issue_labeled");
    expect(job.issueNumber).toBe(7);
  });

  it("skips a non-allowlisted repo", async () => {
    const { deps: d, enqueue } = deps({ allowlist: [] });
    const res = await handleIssueLabeled(baseEvent, d);
    expect(res).toMatchObject({ action: "skipped", reason: "repo not allowlisted" });
    expect(enqueue).not.toHaveBeenCalled();
  });

  it("skips when no trigger label present", async () => {
    const { deps: d } = deps();
    const res = await handleIssueLabeled({ ...baseEvent, labels: ["bug"] }, d);
    expect(res).toMatchObject({ action: "skipped", reason: "no trigger label" });
  });

  it("skips a bot actor", async () => {
    const { deps: d } = deps();
    const res = await handleIssueLabeled(
      { ...baseEvent, actor: { login: "bot", type: "Bot" } },
      d,
    );
    expect(res).toMatchObject({ action: "skipped", reason: "actor not permitted" });
  });
});
