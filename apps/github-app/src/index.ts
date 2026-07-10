/**
 * github-app entrypoint: assemble the production app (health + verified webhook
 * pipeline), start listening, and wire smee forwarding.
 */
import express from "express";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import type { AllowlistEntry } from "@itpr/shared-types";
import { loadConfig } from "@itpr/config";
import { loadAppConfig } from "./config.js";
import { healthRouter } from "./routes/health.js";
import { createWebhookRouter } from "./routes/webhook.js";
import { WebhookVerifier } from "./github/webhook-verifier.js";
import { createEnqueuer } from "./queue/enqueue-job.js";
import { loadAllowedLabels } from "./filters/label-filter.js";
import { startSmee } from "./smee-client.js";
import { logger } from "./logging/logger.js";

const here = dirname(fileURLToPath(import.meta.url));
const POLICIES = resolve(here, "../../../policies");

function main(): void {
  const appConfig = loadAppConfig();
  const cfg = loadConfig();

  const allowedLabels = loadAllowedLabels(resolve(POLICIES, "allowed-labels.yaml"));
  // Repo allowlist is wired from policy in a later phase; deny-all until then.
  const allowlist: AllowlistEntry[] = [];
  if (allowlist.length === 0) {
    logger.warn("repo allowlist is empty — all repos denied until configured");
  }

  const app = express();
  app.use(healthRouter());
  app.use(
    createWebhookRouter({
      verifier: new WebhookVerifier({ secret: cfg.GITHUB_WEBHOOK_SECRET }),
      handlerDeps: {
        enqueuer: createEnqueuer(),
        filters: { allowedLabels, allowlist },
      },
    }),
  );

  const server = app.listen(appConfig.port, () => {
    logger.info("github-app listening", { port: appConfig.port });
    startSmee(appConfig.smeeUrl, `http://localhost:${appConfig.port}/webhook`);
  });

  const shutdown = (signal: string) => {
    logger.info("shutting down", { signal });
    server.close(() => process.exit(0));
  };
  process.on("SIGINT", () => shutdown("SIGINT"));
  process.on("SIGTERM", () => shutdown("SIGTERM"));
}

main();
