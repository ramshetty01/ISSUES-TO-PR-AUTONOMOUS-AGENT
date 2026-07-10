/**
 * github-app entrypoint: assemble the production app (health + verified webhook
 * pipeline), start listening, and wire smee forwarding.
 */
import express from "express";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import type { Job } from "@itpr/shared-types";
import { loadConfig } from "@itpr/config";
import {
  createApp,
  getInstallationPermissions,
  installationClient,
} from "@itpr/github-client";
import { loadAppConfig } from "./config.js";
import { healthRouter } from "./routes/health.js";
import { createWebhookRouter } from "./routes/webhook.js";
import { WebhookVerifier } from "./github/webhook-verifier.js";
import { verifyPermissions } from "./github/permissions.js";
import { postAck } from "./github/comments.js";
import { createEnqueuer } from "./queue/enqueue-job.js";
import { loadAllowedLabels } from "./filters/label-filter.js";
import { loadAllowlist } from "./filters/repo-allowlist.js";
import { startSmee } from "./smee-client.js";
import { logger } from "./logging/logger.js";

const here = dirname(fileURLToPath(import.meta.url));
const POLICIES = resolve(here, "../../../policies");

function main(): void {
  const appConfig = loadAppConfig();
  const cfg = loadConfig();
  const app = createApp(cfg);

  const allowedLabels = loadAllowedLabels(resolve(POLICIES, "allowed-labels.yaml"));
  const allowlist = loadAllowlist(resolve(POLICIES, "repo-allowlist.yaml"));
  if (allowlist.length === 0) {
    logger.warn("repo allowlist is empty — all repos denied until configured");
  }

  const server = express();
  server.use(healthRouter());
  server.use(
    createWebhookRouter({
      verifier: new WebhookVerifier({ secret: cfg.GITHUB_WEBHOOK_SECRET }),
      handlerDeps: {
        enqueuer: createEnqueuer(),
        filters: { allowedLabels, allowlist },
        // Installation permission gate: the agent needs issues/PRs/contents write.
        checkPermissions: async (job: Job) => {
          const perms = await getInstallationPermissions(app, job.installationId);
          return verifyPermissions(perms);
        },
        // Best-effort acknowledgement comment on the triggering issue/PR.
        ack: async ({ job, message }) => {
          const number = job.issueNumber ?? job.prNumber;
          if (!number) return;
          const gh = await installationClient(app, job.installationId);
          await postAck(gh, { owner: job.repo.owner, repo: job.repo.name }, number, message);
        },
      },
    }),
  );

  const listening = server.listen(appConfig.port, () => {
    logger.info("github-app listening", { port: appConfig.port });
    startSmee(appConfig.smeeUrl, `http://localhost:${appConfig.port}/webhook`);
  });

  const shutdown = (signal: string) => {
    logger.info("shutting down", { signal });
    listening.close(() => process.exit(0));
  };
  process.on("SIGINT", () => shutdown("SIGINT"));
  process.on("SIGTERM", () => shutdown("SIGTERM"));
}

main();
