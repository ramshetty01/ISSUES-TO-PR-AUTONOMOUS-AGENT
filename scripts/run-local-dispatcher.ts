/**
 * run-local-dispatcher.ts — start the dispatcher locally. It polls the SQS
 * queue, applies the budget + branch-protection gates, and runs the worker
 * container per job. Validates the environment first (including that the worker
 * image exists) so failures surface immediately.
 *
 *   pnpm dlx tsx scripts/run-local-dispatcher.ts
 *
 * Prereqs: .env populated, LocalStack up (SQS/DynamoDB/S3), and the worker
 * image built (scripts/build-worker-image.sh).
 */
import { spawn, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { loadConfig, ConfigError } from "@itpr/config";

const here = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(here, "..");
const IMAGE = process.env.WORKER_IMAGE_TAG ?? "itpr-worker:local";

function preflight(): void {
  try {
    const cfg = loadConfig();
    console.log(`queue:  ${cfg.SQS_QUEUE_URL}`);
    console.log(`dlq:    ${cfg.SQS_DLQ_URL}`);
    console.log(`budget: ${cfg.DYNAMODB_BUDGET_TABLE}`);
  } catch (err) {
    if (err instanceof ConfigError) {
      console.error("Environment is not ready:\n" + err.message);
      process.exit(1);
    }
    throw err;
  }

  const check = spawnSync("docker", ["image", "inspect", IMAGE], {
    stdio: "ignore",
  });
  if (check.status !== 0) {
    console.error(
      `worker image "${IMAGE}" not found — build it with ` +
        "scripts/build-worker-image.sh before starting the dispatcher.",
    );
    process.exit(1);
  }
  console.log(`worker image: ${IMAGE}`);
}

function main(): void {
  preflight();
  console.log("starting @itpr/dispatcher (Ctrl-C to stop)...");
  const child = spawn("pnpm", ["--filter", "@itpr/dispatcher", "dev"], {
    cwd: ROOT,
    stdio: "inherit",
    env: process.env,
  });
  child.on("exit", (code) => process.exit(code ?? 0));
}

main();
