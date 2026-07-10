/**
 * Enqueue a Job onto SQS (LocalStack in dev). The delivery id rides along as a
 * message attribute + is the Job id, giving the dispatcher an idempotency key.
 */
import { SQSClient, SendMessageCommand } from "@aws-sdk/client-sqs";
import type { Job } from "@itpr/shared-types";
import { loadConfig } from "@itpr/config";

/** Minimal SQS surface, so tests can inject a mock. */
export interface SqsSender {
  send(cmd: SendMessageCommand): Promise<{ MessageId?: string }>;
}

export class JobEnqueuer {
  constructor(
    private readonly sqs: SqsSender,
    private readonly queueUrl: string,
  ) {}

  /** Send the Job; returns the SQS message id. */
  async enqueue(job: Job): Promise<string> {
    const res = await this.sqs.send(
      new SendMessageCommand({
        QueueUrl: this.queueUrl,
        MessageBody: JSON.stringify(job),
        MessageAttributes: {
          deliveryId: { DataType: "String", StringValue: job.id },
          trigger: { DataType: "String", StringValue: job.trigger },
        },
      }),
    );
    return res.MessageId ?? "";
  }
}

/** Build a JobEnqueuer wired to the configured LocalStack SQS endpoint. */
export function createEnqueuer(source?: NodeJS.ProcessEnv): JobEnqueuer {
  const cfg = loadConfig(source);
  const sqs = new SQSClient({
    endpoint: cfg.AWS_ENDPOINT_URL,
    region: cfg.AWS_REGION,
    credentials: {
      accessKeyId: cfg.AWS_ACCESS_KEY_ID,
      secretAccessKey: cfg.AWS_SECRET_ACCESS_KEY,
    },
  });
  return new JobEnqueuer(sqs, cfg.SQS_QUEUE_URL);
}
