/**
 * Resource + isolation limits for the worker container (replaces Fargate task
 * sizing). Mirrors docs/sandbox-design.md: bounded memory/cpu/pids, restricted
 * network, read-only rootfs, dropped capabilities, seccomp.
 */

export type NetworkMode = "none" | "bridge" | string;

export interface ContainerLimits {
  /** e.g. "2g". */
  memory: string;
  /** Fractional CPUs, e.g. "1.5". */
  cpus: string;
  pidsLimit: number;
  network: NetworkMode;
  readonlyRootfs: boolean;
  /** Capabilities to drop; "ALL" drops everything. */
  capDrop: string[];
  /** --security-opt values (e.g. no-new-privileges, seccomp profile). */
  securityOpt: string[];
  /** Writable tmpfs mounts for a read-only rootfs (e.g. /tmp, workspace). */
  tmpfs: string[];
}

export const DEFAULT_LIMITS: ContainerLimits = {
  memory: "2g",
  cpus: "2",
  pidsLimit: 512,
  network: "bridge",
  readonlyRootfs: true,
  capDrop: ["ALL"],
  securityOpt: ["no-new-privileges"],
  tmpfs: ["/tmp", "/workspace"],
};

/** Translate limits into `docker run` argument tokens. */
export function toDockerArgs(limits: ContainerLimits): string[] {
  const args: string[] = [
    "--memory", limits.memory,
    "--cpus", limits.cpus,
    "--pids-limit", String(limits.pidsLimit),
    "--network", limits.network,
  ];
  if (limits.readonlyRootfs) args.push("--read-only");
  for (const c of limits.capDrop) args.push("--cap-drop", c);
  for (const s of limits.securityOpt) args.push("--security-opt", s);
  for (const t of limits.tmpfs) args.push("--tmpfs", t);
  return args;
}
