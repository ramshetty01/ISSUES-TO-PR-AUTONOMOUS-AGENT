import { describe, it, expect, vi } from "vitest";
import {
  ReceiveMessageCommand,
  DeleteMessageCommand,
  ChangeMessageVisibilityCommand,
  SendMessageCommand,
} from "@aws-sdk/client-sqs";
import type { Job } from "@itpr/shared-types";
import { receiveJobs, type SqsApi } from "../src/queue/sqs-client.js";
import { ackMessage } from "../src/queue/ack.js";
import { nackMessage } from "../src/queue/nack.js";
import {
  routeToDeadLetter,
  shouldDeadLetter,
} from "../src/queue/dead-letter.js";

const QUEUE = "http://localhost:4566/000000000000/itpr-jobs";
const DLQ = "http://localhost:4566/000000000000/itpr-jobs-dlq";

const job: Job = {
  id: "d-1",
  repo: { owner: "acme", name: "widgets" },
  installationId: 42,
  trigger: "issue_labeled",
  issueNumber: 7,
  headSha: "",
  labels: ["agent-fix"],
  createdAt: "2026-07-10T12:00:00.000Z",
};

describe("receiveJobs", () => {
  it("parses message bodies into jobs with receive count", async () => {
    const send = vi.fn().mockResolvedValue({
      Messages: [
        {
          MessageId: "m1",
          ReceiptHandle: "rh1",
          Body: JSON.stringify(job),
          Attributes: { ApproximateReceiveCount: "2" },
        },
      ],
    });
    const sqs: SqsApi = { send };
    const jobs = await receiveJobs(sqs, QUEUE);
    expect(send.mock.calls[0]![0]).toBeInstanceOf(ReceiveMessageCommand);
    expect(jobs).toHaveLength(1);
    expect(jobs[0]!.job).toEqual(job);
    expect(jobs[0]!.receiveCount).toBe(2);
    expect(jobs[0]!.receiptHandle).toBe("rh1");
  });

  it("skips malformed messages", async () => {
    const send = vi.fn().mockResolvedValue({
      Messages: [{ MessageId: "m2", ReceiptHandle: "rh2", Body: "not-json" }],
    });
    const jobs = await receiveJobs({ send }, QUEUE);
    expect(jobs).toHaveLength(0);
  });

  it("returns empty on no messages", async () => {
    const jobs = await receiveJobs({ send: vi.fn().mockResolvedValue({}) }, QUEUE);
    expect(jobs).toEqual([]);
  });
});

describe("ack / nack", () => {
  it("ack deletes the message", async () => {
    const send = vi.fn().mockResolvedValue({});
    await ackMessage({ send }, QUEUE, "rh1");
    const cmd = send.mock.calls[0]![0];
    expect(cmd).toBeInstanceOf(DeleteMessageCommand);
    expect(cmd.input).toMatchObject({ QueueUrl: QUEUE, ReceiptHandle: "rh1" });
  });

  it("nack resets visibility (default 0 = immediate redelivery)", async () => {
    const send = vi.fn().mockResolvedValue({});
    await nackMessage({ send }, QUEUE, "rh1");
    const cmd = send.mock.calls[0]![0];
    expect(cmd).toBeInstanceOf(ChangeMessageVisibilityCommand);
    expect(cmd.input.VisibilityTimeout).toBe(0);
  });

  it("nack applies a backoff delay", async () => {
    const send = vi.fn().mockResolvedValue({});
    await nackMessage({ send }, QUEUE, "rh1", 30);
    expect(send.mock.calls[0]![0].input.VisibilityTimeout).toBe(30);
  });
});

describe("dead-letter", () => {
  it("shouldDeadLetter triggers at the max receive count", () => {
    expect(shouldDeadLetter(4)).toBe(false);
    expect(shouldDeadLetter(5)).toBe(true);
    expect(shouldDeadLetter(2, 2)).toBe(true);
  });

  it("routes to DLQ then deletes the original", async () => {
    const send = vi.fn().mockResolvedValue({});
    await routeToDeadLetter({ send }, {
      dlqUrl: DLQ,
      queueUrl: QUEUE,
      receiptHandle: "rh1",
      job,
      reason: "max receives exceeded",
    });
    const first = send.mock.calls[0]![0];
    const second = send.mock.calls[1]![0];
    expect(first).toBeInstanceOf(SendMessageCommand);
    expect(first.input.QueueUrl).toBe(DLQ);
    expect(JSON.parse(first.input.MessageBody)).toEqual(job);
    expect(second).toBeInstanceOf(DeleteMessageCommand);
    expect(second.input.ReceiptHandle).toBe("rh1");
  });
});
