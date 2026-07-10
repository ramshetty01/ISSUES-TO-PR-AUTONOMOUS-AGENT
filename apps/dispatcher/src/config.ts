/** Dispatcher runtime config derived from the shared config. */
import { loadConfig } from "@itpr/config";

export interface DispatcherConfig {
  queueUrl: string;
  dlqUrl: string;
  workerImage: string;
  maxReceives: number;
  pollWaitSeconds: number;
  workerTimeoutMs: number;
}

export function loadDispatcherConfig(source?: NodeJS.ProcessEnv): DispatcherConfig {
  const cfg = loadConfig(source);
  return {
    queueUrl: cfg.SQS_QUEUE_URL,
    dlqUrl: cfg.SQS_DLQ_URL,
    workerImage: "itpr-worker",
    maxReceives: 5,
    pollWaitSeconds: 10,
    workerTimeoutMs: 15 * 60_000,
  };
}
