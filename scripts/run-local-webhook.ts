/**
 * run-local-webhook.ts — start the github-app locally (webhook receiver +
 * smee forwarder). Validates the environment up front so misconfiguration
 * fails with a readable error instead of a stack trace mid-request, then hands
 * off to the app's dev entrypoint.
 *
 *   pnpm dlx tsx scripts/run-local-webhook.ts
 *
 * Prereqs: .env populated (scripts/setup-github-app.sh), a smee channel
 * (scripts/setup-smee.sh), and LocalStack up for the SQS queue.
 */
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { loadConfig, ConfigError } from "@itpr/config";

const here = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(here, "..");

function preflight(): void {
  try {
    const cfg = loadConfig();
    if (!cfg.SMEE_URL) {
      console.warn(
        "warning: SMEE_URL is not set — GitHub webhooks will not reach this " +
          "process. Run scripts/setup-smee.sh first.",
      );
    } else {
      console.log(`smee channel: ${cfg.SMEE_URL}`);
    }
    console.log(`queue: ${cfg.SQS_QUEUE_URL}`);
  } catch (err) {
    if (err instanceof ConfigError) {
      console.error("Environment is not ready:\n" + err.message);
      process.exit(1);
    }
    throw err;
  }
}

function main(): void {
  preflight();
  console.log("starting @itpr/github-app (Ctrl-C to stop)...");
  const child = spawn("pnpm", ["--filter", "@itpr/github-app", "dev"], {
    cwd: ROOT,
    stdio: "inherit",
    env: process.env,
  });
  child.on("exit", (code) => process.exit(code ?? 0));
}

main();
