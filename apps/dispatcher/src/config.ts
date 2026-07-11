/** Dispatcher runtime config derived from the shared config. */
import { loadConfig } from "@itpr/config";

export interface DispatcherConfig {
  queueUrl: string;
  dlqUrl: string;
  workerImage: string;
  workerNetwork: string;
  maxReceives: number;
  pollWaitSeconds: number;
  workerTimeoutMs: number;
}

export function loadDispatcherConfig(source?: NodeJS.ProcessEnv): DispatcherConfig {
  const cfg = loadConfig(source);
  return {
    queueUrl: cfg.SQS_QUEUE_URL,
    dlqUrl: cfg.SQS_DLQ_URL,
    workerImage: source?.WORKER_IMAGE_TAG ?? process.env.WORKER_IMAGE_TAG ?? "itpr-worker:local",
    workerNetwork: source?.WORKER_DOCKER_NETWORK ?? process.env.WORKER_DOCKER_NETWORK ?? "itpr-local",
    maxReceives: 5,
    pollWaitSeconds: 10,
    workerTimeoutMs: 15 * 60_000,
  };
}
