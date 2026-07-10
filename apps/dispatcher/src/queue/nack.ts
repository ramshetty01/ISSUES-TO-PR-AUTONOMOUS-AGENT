/**
 * Negative-ack: return a message to the queue for redelivery by resetting its
 * visibility timeout. An optional delay backs off retries.
 */
import { ChangeMessageVisibilityCommand } from "@aws-sdk/client-sqs";
import type { SqsApi } from "./sqs-client.js";

export async function nackMessage(
  sqs: SqsApi,
  queueUrl: string,
  receiptHandle: string,
  delaySeconds = 0,
): Promise<void> {
  await sqs.send(
    new ChangeMessageVisibilityCommand({
      QueueUrl: queueUrl,
      ReceiptHandle: receiptHandle,
      VisibilityTimeout: Math.max(0, Math.floor(delaySeconds)),
    }),
  );
}
