import { describe, it, expect, vi } from "vitest";
import { SendMessageCommand } from "@aws-sdk/client-sqs";
import { buildJob } from "../src/queue/job-payload.js";
import { JobEnqueuer, type SqsSender } from "../src/queue/enqueue-job.js";

const REPO = { owner: "acme", name: "widgets" };
const fixedNow = () => new Date("2026-07-10T12:00:00Z");

describe("buildJob", () => {
  it("maps an issue_labeled event to a Job", () => {
    const job = buildJob({
      deliveryId: "d-1",
      repo: REPO,
      installationId: 42,
      trigger: "issue_labeled",
      issueNumber: 7,
      labels: ["agent-fix"],
      now: fixedNow,
    });
    expect(job).toEqual({
      id: "d-1",
      repo: REPO,
      installationId: 42,
      trigger: "issue_labeled",
      issueNumber: 7,
      headSha: "",
      labels: ["agent-fix"],
      createdAt: "2026-07-10T12:00:00.000Z",
    });
    expect(job).not.toHaveProperty("prNumber");
  });

  it("maps a pr_comment event with prNumber", () => {
    const job = buildJob({
      deliveryId: "d-2",
      repo: REPO,
      installationId: 42,
      trigger: "pr_comment",
      prNumber: 15,
      labels: [],
      headSha: "abc123",
      now: fixedNow,
    });
    expect(job.trigger).toBe("pr_comment");
    expect(job.prNumber).toBe(15);
    expect(job.headSha).toBe("abc123");
  });
});

describe("JobEnqueuer", () => {
  it("sends the job body + delivery id attribute and returns the message id", async () => {
    const send = vi.fn().mockResolvedValue({ MessageId: "m-99" });
    const sqs: SqsSender = { send };
    const enqueuer = new JobEnqueuer(sqs, "http://localhost:4566/000000000000/itpr-jobs");

    const job = buildJob({
      deliveryId: "d-1",
      repo: REPO,
      installationId: 42,
      trigger: "issue_labeled",
      issueNumber: 7,
      labels: ["agent-fix"],
      now: fixedNow,
    });
    const id = await enqueuer.enqueue(job);

    expect(id).toBe("m-99");
    expect(send).toHaveBeenCalledOnce();
    const cmd = send.mock.calls[0]![0] as SendMessageCommand;
    expect(cmd).toBeInstanceOf(SendMessageCommand);
    expect(cmd.input.QueueUrl).toContain("itpr-jobs");
    expect(JSON.parse(cmd.input.MessageBody!)).toEqual(job);
    expect(cmd.input.MessageAttributes!.deliveryId!.StringValue).toBe("d-1");
    expect(cmd.input.MessageAttributes!.trigger!.StringValue).toBe("issue_labeled");
  });
});
