/**
 * Dead-letter routing. SQS can redrive automatically, but the dispatcher also
 * makes an explicit decision so poison messages never loop: past the max
 * receive count, forward the job to the DLQ and ack the original.
 */
import { SendMessageCommand } from "@aws-sdk/client-sqs";
import type { Job } from "@itpr/shared-types";
import type { SqsApi } from "./sqs-client.js";
import { ackMessage } from "./ack.js";

export const DEFAULT_MAX_RECEIVES = 5;

/** True when a message has been delivered too many times. */
export function shouldDeadLetter(
  receiveCount: number,
  maxReceives = DEFAULT_MAX_RECEIVES,
): boolean {
  return receiveCount >= maxReceives;
}

/** Forward a job to the DLQ, then delete it from the main queue. */
export async function routeToDeadLetter(
  sqs: SqsApi,
  args: {
    dlqUrl: string;
    queueUrl: string;
    receiptHandle: string;
    job: Job;
    reason: string;
  },
): Promise<void> {
  await sqs.send(
    new SendMessageCommand({
      QueueUrl: args.dlqUrl,
      MessageBody: JSON.stringify(args.job),
      MessageAttributes: {
        deadLetterReason: { DataType: "String", StringValue: args.reason },
        deliveryId: { DataType: "String", StringValue: args.job.id },
      },
    }),
  );
  await ackMessage(sqs, args.queueUrl, args.receiptHandle);
}
