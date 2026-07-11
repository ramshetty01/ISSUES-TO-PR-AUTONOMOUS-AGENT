/**
 * Dispatcher entrypoint: wire the queue, budget, repo-policy, and docker runner
 * into the poll loop, then run until terminated.
 */
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { loadConfig } from "@itpr/config";
import {
  createApp,
  installationClient,
  getInstallationToken,
  getDefaultBranch,
} from "@itpr/github-client";
import { loadDispatcherConfig } from "./config.js";
import { createSqsClient, receiveJobs } from "./queue/sqs-client.js";
import { ackMessage } from "./queue/ack.js";
import { nackMessage } from "./queue/nack.js";
import { routeToDeadLetter } from "./queue/dead-letter.js";
import { BudgetService } from "./budget/budget-service.js";
import { createLedger } from "./budget/budget-ledger.js";
import { loadBudgetDefaults } from "./budget/budget-policy.js";
import {
  evaluateRepoProtection,
  loadRequiredProtection,
} from "./repo-policy/branch-protection-check.js";
import {
  loadRetryPolicy,
  nextDelayMs,
} from "./repo-policy/retry-policy.js";
import { runDockerWorker } from "./runner/run-docker-worker.js";
import { Dispatcher } from "./dispatcher.js";
import { Poller } from "./poller.js";
import { AuditLog } from "./observability/audit-log.js";
import { Metrics } from "./observability/metrics.js";
import { logger } from "./logging/logger.js";

const here = dirname(fileURLToPath(import.meta.url));
const POLICIES = resolve(here, "../../../policies");

async function main(): Promise<void> {
  const cfg = loadConfig();
  const dcfg = loadDispatcherConfig();
  const sqs = createSqsClient();
  const app = createApp(cfg);

  const budgetService = new BudgetService({
    ledger: createLedger(),
    defaults: loadBudgetDefaults(resolve(POLICIES, "budget-defaults.yaml")),
  });
  const required = loadRequiredProtection(
    resolve(POLICIES, "branch-protection-required.yaml"),
  );
  const retry = loadRetryPolicy(resolve(POLICIES, "retry-policy.yaml"));

  const dispatcher = new Dispatcher({
    checkBudget: (job) => budgetService.checkAndReserve(job),
    checkRepoPolicy: async (job) => {
      const gh = await installationClient(app, job.installationId);
      const branch = await getDefaultBranch(gh, {
        owner: job.repo.owner,
        repo: job.repo.name,
      });
      const res = await evaluateRepoProtection(gh, job.repo, branch, required);
      return res.ok ? { ok: true } : { ok: false, reason: res.missing.join("; ") };
    },
    runWorker: async (job) => {
      const token = await getInstallationToken(app, job.installationId);
      const handle = runDockerWorker(job, {
        image: dcfg.workerImage,
        network: dcfg.workerNetwork,
        installationToken: token.token,
        timeoutMs: dcfg.workerTimeoutMs,
      });
      return handle.done;
    },
    ack: (r) => ackMessage(sqs, dcfg.queueUrl, r.receiptHandle),
    nack: (r) =>
      nackMessage(
        sqs,
        dcfg.queueUrl,
        r.receiptHandle,
        Math.round(nextDelayMs(r.receiveCount, retry) / 1000),
      ),
    deadLetter: (r, reason) =>
      routeToDeadLetter(sqs, {
        dlqUrl: dcfg.dlqUrl,
        queueUrl: dcfg.queueUrl,
        receiptHandle: r.receiptHandle,
        job: r.job,
        reason,
      }),
    maxReceives: dcfg.maxReceives,
    audit: new AuditLog(),
    metrics: new Metrics(),
  });

  const poller = new Poller({
    receive: () =>
      receiveJobs(sqs, dcfg.queueUrl, { waitTimeSeconds: dcfg.pollWaitSeconds }),
    dispatcher,
  });

  const shutdown = (signal: string) => {
    logger.info("shutting down", { signal });
    poller.stop();
  };
  process.on("SIGINT", () => shutdown("SIGINT"));
  process.on("SIGTERM", () => shutdown("SIGTERM"));

  await poller.run();
}

main().catch((err) => {
  logger.error("dispatcher crashed", { error: String(err) });
  process.exit(1);
});
