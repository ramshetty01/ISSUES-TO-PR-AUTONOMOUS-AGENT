/** Acknowledge a successfully-processed message by deleting it. */
import { DeleteMessageCommand } from "@aws-sdk/client-sqs";
import type { SqsApi } from "./sqs-client.js";

export async function ackMessage(
  sqs: SqsApi,
  queueUrl: string,
  receiptHandle: string,
): Promise<void> {
  await sqs.send(
    new DeleteMessageCommand({ QueueUrl: queueUrl, ReceiptHandle: receiptHandle }),
  );
}
