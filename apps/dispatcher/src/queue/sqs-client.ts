/**
 * SQS receive primitives for the dispatcher. Long-polls the jobs queue and
 * parses message bodies into Jobs, carrying the receipt handle + receive count
 * needed for ack/nack/dead-letter decisions.
 */
import {
  SQSClient,
  ReceiveMessageCommand,
  type Message,
} from "@aws-sdk/client-sqs";
import type { Job } from "@itpr/shared-types";
import { loadConfig } from "@itpr/config";

/** Minimal SQS surface so tests can inject a mock. */
export interface SqsApi {
  send(command: unknown): Promise<unknown>;
}

export interface ReceivedJob {
  messageId: string;
  receiptHandle: string;
  job: Job;
  /** SQS ApproximateReceiveCount for this message. */
  receiveCount: number;
}

export interface ReceiveOptions {
  maxMessages?: number;
  waitTimeSeconds?: number;
  visibilityTimeoutSeconds?: number;
}

/** Long-poll the queue and return parsed jobs (skips unparseable messages). */
export async function receiveJobs(
  sqs: SqsApi,
  queueUrl: string,
  opts: ReceiveOptions = {},
): Promise<ReceivedJob[]> {
  const res = (await sqs.send(
    new ReceiveMessageCommand({
      QueueUrl: queueUrl,
      MaxNumberOfMessages: opts.maxMessages ?? 5,
      WaitTimeSeconds: opts.waitTimeSeconds ?? 10,
      VisibilityTimeout: opts.visibilityTimeoutSeconds ?? 300,
      MessageSystemAttributeNames: ["ApproximateReceiveCount"],
      MessageAttributeNames: ["All"],
    }),
  )) as { Messages?: Message[] };

  const out: ReceivedJob[] = [];
  for (const m of res.Messages ?? []) {
    if (!m.Body || !m.ReceiptHandle) continue;
    let job: Job;
    try {
      job = JSON.parse(m.Body) as Job;
    } catch {
      continue; // malformed; leave for redrive/DLQ
    }
    out.push({
      messageId: m.MessageId ?? "",
      receiptHandle: m.ReceiptHandle,
      job,
      receiveCount: Number(m.Attributes?.ApproximateReceiveCount ?? "1"),
    });
  }
  return out;
}

/** Build an SQS client wired to the configured endpoint (LocalStack in dev). */
export function createSqsClient(source?: NodeJS.ProcessEnv): SQSClient {
  const cfg = loadConfig(source);
  return new SQSClient({
    endpoint: cfg.AWS_ENDPOINT_URL,
    region: cfg.AWS_REGION,
    credentials: {
      accessKeyId: cfg.AWS_ACCESS_KEY_ID,
      secretAccessKey: cfg.AWS_SECRET_ACCESS_KEY,
    },
  });
}
