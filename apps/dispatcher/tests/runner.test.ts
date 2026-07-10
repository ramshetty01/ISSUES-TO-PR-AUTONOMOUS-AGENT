import { describe, it, expect, vi } from "vitest";
import { EventEmitter } from "node:events";
import type { Job } from "@itpr/shared-types";
import {
  DEFAULT_LIMITS,
  toDockerArgs,
} from "../src/runner/container-limits.js";
import { buildWorkerEnv } from "../src/runner/worker-env.js";
import { waitForExit, type ChildLike } from "../src/runner/worker-status.js";
import {
  buildRunArgs,
  runDockerWorker,
} from "../src/runner/run-docker-worker.js";

const job: Job = {
  id: "d-1",
  repo: { owner: "acme", name: "widgets" },
  installationId: 42,
  trigger: "issue_labeled",
  issueNumber: 7,
  headSha: "",
  labels: ["agent-fix"],
  createdAt: "2026-07-10T12:00:00.000Z",
};

const ENV_SOURCE = {
  NODE_ENV: "development",
  GITHUB_APP_ID: "1",
  GITHUB_APP_PRIVATE_KEY: "k",
  GITHUB_WEBHOOK_SECRET: "s",
} as NodeJS.ProcessEnv;

class FakeChild extends EventEmitter {
  killed = false;
  kill(): boolean {
    this.killed = true;
    return true;
  }
}

describe("container-limits", () => {
  it("emits every isolation flag", () => {
    const args = toDockerArgs(DEFAULT_LIMITS);
    const s = args.join(" ");
    expect(s).toContain("--memory 2g");
    expect(s).toContain("--cpus 2");
    expect(s).toContain("--pids-limit 512");
    expect(s).toContain("--network bridge");
    expect(args).toContain("--read-only");
    expect(s).toContain("--cap-drop ALL");
    expect(s).toContain("--security-opt no-new-privileges");
  });
});

describe("worker-env", () => {
  it("includes the token + endpoints in the env map", () => {
    const { env, keys } = buildWorkerEnv({
      job,
      installationToken: "ghs_secret",
      source: ENV_SOURCE,
    });
    expect(env.GITHUB_INSTALLATION_TOKEN).toBe("ghs_secret");
    expect(env.ITPR_JOB_ID).toBe("d-1");
    expect(env.AWS_ENDPOINT_URL).toContain("4566");
    expect(keys).toContain("GITHUB_INSTALLATION_TOKEN");
  });
});

describe("buildRunArgs", () => {
  it("passes env names only (no secret values in argv), image last", () => {
    const argv = buildRunArgs({
      image: "itpr-worker",
      containerName: "itpr-worker-d-1",
      limits: DEFAULT_LIMITS,
      envKeys: ["GITHUB_INSTALLATION_TOKEN", "ITPR_JOB_ID"],
    });
    expect(argv[0]).toBe("run");
    expect(argv).toContain("--name");
    expect(argv).toContain("itpr-worker-d-1");
    expect(argv).toContain("-e");
    expect(argv).toContain("GITHUB_INSTALLATION_TOKEN");
    // secret value must never appear as an argv token
    expect(argv).not.toContain("ghs_secret");
    expect(argv[argv.length - 1]).toBe("itpr-worker");
  });
});

describe("waitForExit", () => {
  it("resolves with the exit code on close", async () => {
    const child = new FakeChild();
    const p = waitForExit(child as unknown as ChildLike, 1000);
    child.emit("close", 0);
    expect(await p).toEqual({ exitCode: 0, timedOut: false });
  });

  it("kills and reports timeout", async () => {
    const child = new FakeChild();
    const p = waitForExit(child as unknown as ChildLike, 5);
    const res = await p;
    expect(res.timedOut).toBe(true);
    expect(child.killed).toBe(true);
  });
});

describe("runDockerWorker", () => {
  it("spawns docker with limits + env names, keeping secrets out of argv", async () => {
    const child = new FakeChild();
    const spawnFn = vi.fn().mockReturnValue(child);

    const handle = runDockerWorker(job, {
      image: "itpr-worker",
      installationToken: "ghs_secret",
      timeoutMs: 1000,
      source: ENV_SOURCE,
      spawnFn: spawnFn as never,
    });

    expect(spawnFn).toHaveBeenCalledOnce();
    const [cmd, argv, spawnOpts] = spawnFn.mock.calls[0]!;
    expect(cmd).toBe("docker");
    expect(argv).not.toContain("ghs_secret");
    expect(spawnOpts.env.GITHUB_INSTALLATION_TOKEN).toBe("ghs_secret");
    expect(handle.containerName).toBe("itpr-worker-d-1");

    child.emit("close", 0);
    expect(await handle.done).toEqual({ exitCode: 0, timedOut: false });
  });
});
