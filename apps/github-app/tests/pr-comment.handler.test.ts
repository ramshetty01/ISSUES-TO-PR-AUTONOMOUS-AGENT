import { describe, it, expect, vi } from "vitest";
import type { PrCommentEvent } from "@itpr/shared-types";
import {
  handlePrComment,
  hasCommand,
} from "../src/handlers/pr-comment.handler.js";
import type { HandlerDeps } from "../src/handlers/issue-labeled.handler.js";

const baseEvent: PrCommentEvent = {
  event: "pr_comment",
  deliveryId: "d-2",
  installationId: 42,
  repo: { owner: "acme", name: "widgets" },
  prNumber: 15,
  body: "please /agent take a look",
  actor: { login: "alice", type: "User" },
};

function mk(): { deps: HandlerDeps; enqueue: ReturnType<typeof vi.fn> } {
  const enqueue = vi.fn().mockResolvedValue("m-2");
  return {
    enqueue,
    deps: {
      enqueuer: { enqueue },
      filters: {
        allowedLabels: [],
        allowlist: [{ owner: "acme", name: "widgets" }],
      },
      now: () => new Date("2026-07-10T12:00:00Z"),
    },
  };
}

describe("hasCommand", () => {
  it("matches the command as a whole word", () => {
    expect(hasCommand("do /agent now", "/agent")).toBe(true);
    expect(hasCommand("/agent", "/agent")).toBe(true);
    expect(hasCommand("nope /agentxyz", "/agent")).toBe(false);
    expect(hasCommand("no command here", "/agent")).toBe(false);
  });
});

describe("handlePrComment", () => {
  it("enqueues a pr_comment job when the command is present", async () => {
    const { deps, enqueue } = mk();
    const res = await handlePrComment(baseEvent, deps);
    expect(res).toEqual({ action: "enqueued", jobId: "d-2", messageId: "m-2" });
    const job = enqueue.mock.calls[0]![0];
    expect(job.trigger).toBe("pr_comment");
    expect(job.prNumber).toBe(15);
  });

  it("skips when the comment has no command", async () => {
    const { deps, enqueue } = mk();
    const res = await handlePrComment({ ...baseEvent, body: "just a comment" }, deps);
    expect(res).toMatchObject({ action: "skipped", reason: "no command in comment" });
    expect(enqueue).not.toHaveBeenCalled();
  });

  it("skips a non-allowlisted repo", async () => {
    const { deps } = mk();
    deps.filters.allowlist = [];
    const res = await handlePrComment(baseEvent, deps);
    expect(res).toMatchObject({ action: "skipped", reason: "repo not allowlisted" });
  });
});
