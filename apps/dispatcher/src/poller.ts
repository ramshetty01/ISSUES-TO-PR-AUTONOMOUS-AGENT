/**
 * Long-poll loop: receive jobs and hand each to the Dispatcher. Stoppable for
 * graceful shutdown + tests.
 */
import type { Dispatcher } from "./dispatcher.js";
import type { ReceivedJob } from "./queue/sqs-client.js";
import { logger } from "./logging/logger.js";

export interface PollerDeps {
  receive: () => Promise<ReceivedJob[]>;
  dispatcher: Dispatcher;
}

export class Poller {
  private running = false;

  constructor(private readonly deps: PollerDeps) {}

  /** Process exactly one receive batch (unit of work; used by run() + tests). */
  async tick(): Promise<number> {
    const batch = await this.deps.receive();
    for (const received of batch) {
      try {
        await this.deps.dispatcher.handle(received);
      } catch (err) {
        logger.error("dispatch threw", { error: String(err), jobId: received.job.id });
      }
    }
    return batch.length;
  }

  /** Loop until stop() is called. */
  async run(): Promise<void> {
    this.running = true;
    logger.info("poller started");
    while (this.running) {
      await this.tick();
    }
    logger.info("poller stopped");
  }

  stop(): void {
    this.running = false;
  }
}
