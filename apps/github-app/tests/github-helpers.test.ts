import { describe, it, expect, vi } from "vitest";
import type { GhRest } from "@itpr/github-client";
import {
  verifyPermissions,
  permissionRefusal,
} from "../src/github/permissions.js";
import { fetchIssueContext } from "../src/github/issues.js";
import { applyLabels } from "../src/github/labels.js";
import { postAck, postAckOnce, alreadyAcked, ACK_MARKER } from "../src/github/comments.js";

const REPO = { owner: "acme", repo: "widgets" };

describe("permissions", () => {
  it("passes when all required scopes are write+", () => {
    const res = verifyPermissions({
      issues: "write",
      pull_requests: "write",
      contents: "admin",
      metadata: "read",
    });
    expect(res.ok).toBe(true);
    expect(res.missing).toEqual([]);
  });

  it("reports missing scopes and builds a refusal message", () => {
    const res = verifyPermissions({ issues: "read", contents: "write" });
    expect(res.ok).toBe(false);
    expect(res.missing).toContain("issues");
    expect(res.missing).toContain("pull_requests");
    const msg = permissionRefusal(res.missing);
    expect(msg).toContain("issues:write");
    expect(msg).toContain("pull_requests:write");
  });
});

describe("issues", () => {
  it("fetches issue context via the installation client", async () => {
    const get = vi.fn().mockResolvedValue({
      data: { title: "bug", body: "broken", state: "open" },
    });
    const gh = { issues: { get } } as unknown as GhRest;
    const ctx = await fetchIssueContext(gh, REPO, 7);
    expect(get).toHaveBeenCalledWith({ ...REPO, issue_number: 7 });
    expect(ctx).toEqual({ number: 7, title: "bug", body: "broken", state: "open" });
  });
});

describe("labels", () => {
  it("no-ops on empty label list", async () => {
    const addLabels = vi.fn();
    const gh = { issues: { addLabels } } as unknown as GhRest;
    await applyLabels(gh, REPO, 1, []);
    expect(addLabels).not.toHaveBeenCalled();
  });

  it("applies labels when provided", async () => {
    const addLabels = vi.fn().mockResolvedValue({ data: {} });
    const gh = { issues: { addLabels } } as unknown as GhRest;
    await applyLabels(gh, REPO, 1, ["agent-fix"]);
    expect(addLabels).toHaveBeenCalledWith({
      ...REPO,
      issue_number: 1,
      labels: ["agent-fix"],
    });
  });
});

describe("comments (ack dedup)", () => {
  const mkGh = () => {
    const createComment = vi.fn().mockResolvedValue({
      data: { id: 1, html_url: "https://x/comment/1" },
    });
    return { gh: { issues: { createComment } } as unknown as GhRest, createComment };
  };

  it("embeds the marker and posts", async () => {
    const { gh, createComment } = mkGh();
    const url = await postAck(gh, REPO, 1, "on it");
    expect(url).toBe("https://x/comment/1");
    const body = createComment.mock.calls[0]![0].body as string;
    expect(body).toContain(ACK_MARKER);
  });

  it("detects an existing ack", () => {
    expect(alreadyAcked([`hello ${ACK_MARKER}`])).toBe(true);
    expect(alreadyAcked(["nothing here"])).toBe(false);
  });

  it("postAckOnce skips when already acked", async () => {
    const { gh, createComment } = mkGh();
    const skipped = await postAckOnce(gh, REPO, 1, "on it", [`prior ${ACK_MARKER}`]);
    expect(skipped).toBeUndefined();
    expect(createComment).not.toHaveBeenCalled();

    const posted = await postAckOnce(gh, REPO, 1, "on it", ["unrelated"]);
    expect(posted).toBe("https://x/comment/1");
    expect(createComment).toHaveBeenCalledOnce();
  });
});
