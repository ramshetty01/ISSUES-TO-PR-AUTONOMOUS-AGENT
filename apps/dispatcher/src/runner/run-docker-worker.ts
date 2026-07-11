/**
 * Spawn the worker as a resource-limited local Docker container (replaces
 * Fargate/ECS). Secret values ride in the child-process env; only variable
 * names appear in argv.
 */
import { spawn, type ChildProcess } from "node:child_process";
import type { Job } from "@itpr/shared-types";
import {
  DEFAULT_LIMITS,
  toDockerArgs,
  type ContainerLimits,
} from "./container-limits.js";
import { buildWorkerEnv } from "./worker-env.js";
import { waitForExit, type ChildLike, type ExitStatus } from "./worker-status.js";

export interface RunOptions {
  image: string;
  network?: string;
  installationToken: string;
  limits?: ContainerLimits;
  /** Hard timeout in ms; the container is killed past this. */
  timeoutMs?: number;
  source?: NodeJS.ProcessEnv;
  /** Injectable spawn for tests. */
  spawnFn?: typeof spawn;
}

export interface RunHandle {
  containerName: string;
  argv: string[];
  done: Promise<ExitStatus>;
}

/** Build the `docker run` argv (env values are NOT included — names only). */
export function buildRunArgs(args: {
  image: string;
  containerName: string;
  limits: ContainerLimits;
  envKeys: string[];
}): string[] {
  return [
    "run",
    "--rm",
    "--name",
    args.containerName,
    ...toDockerArgs(args.limits),
    ...args.envKeys.flatMap((k) => ["-e", k]),
    args.image,
  ];
}

export function runDockerWorker(job: Job, opts: RunOptions): RunHandle {
  const limits = {
    ...(opts.limits ?? DEFAULT_LIMITS),
    ...(opts.network ? { network: opts.network } : {}),
  };
  const { env, keys } = buildWorkerEnv({
    job,
    installationToken: opts.installationToken,
    ...(opts.source ? { source: opts.source } : {}),
  });
  const containerName = `itpr-worker-${job.id}`;
  const argv = buildRunArgs({ image: opts.image, containerName, limits, envKeys: keys });

  const doSpawn = opts.spawnFn ?? spawn;
  const child = doSpawn("docker", argv, {
    env: { ...process.env, ...env },
    stdio: "inherit",
  }) as ChildProcess;

  const done = waitForExit(child as unknown as ChildLike, opts.timeoutMs ?? 15 * 60_000);
  return { containerName, argv, done };
}
