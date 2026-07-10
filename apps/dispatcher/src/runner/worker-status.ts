/**
 * Track a spawned worker process to completion, enforcing a hard timeout that
 * kills a runaway container.
 */
import type { EventEmitter } from "node:events";

/** The subset of a child process the status watcher relies on. */
export interface ChildLike extends Pick<EventEmitter, "on"> {
  kill(signal?: NodeJS.Signals): boolean;
}

export interface ExitStatus {
  exitCode: number;
  timedOut: boolean;
}

/**
 * Resolve when the child exits, or kill it after `timeoutMs` and resolve with
 * timedOut=true. A null exit code (killed by signal) is reported as 137.
 */
export function waitForExit(
  child: ChildLike,
  timeoutMs: number,
): Promise<ExitStatus> {
  return new Promise((resolve) => {
    let settled = false;
    const finish = (status: ExitStatus) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(status);
    };

    const timer = setTimeout(() => {
      child.kill("SIGKILL");
      finish({ exitCode: 137, timedOut: true });
    }, timeoutMs);

    child.on("close", (code: number | null) => {
      finish({ exitCode: code ?? 137, timedOut: false });
    });
    child.on("error", () => {
      finish({ exitCode: 1, timedOut: false });
    });
  });
}
