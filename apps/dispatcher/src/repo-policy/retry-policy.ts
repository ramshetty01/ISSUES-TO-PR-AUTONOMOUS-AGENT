/**
 * Exponential backoff for transient dispatch failures. Deterministic by default
 * (jitter opt-in) so behavior is testable.
 */
import { readFileSync } from "node:fs";
import { parse } from "yaml";

export interface RetryPolicy {
  maxAttempts: number;
  baseDelayMs: number;
  maxDelayMs: number;
  factor: number;
  /** Add full jitter (random in [0, delay]). Off by default. */
  jitter?: boolean;
}

export const DEFAULT_RETRY_POLICY: RetryPolicy = {
  maxAttempts: 5,
  baseDelayMs: 1000,
  maxDelayMs: 60_000,
  factor: 2,
};

/** Whether another attempt is allowed. `attempt` is 1-based (attempts made). */
export function shouldRetry(attempt: number, policy: RetryPolicy): boolean {
  return attempt < policy.maxAttempts;
}

/**
 * Delay before the next attempt. `attempt` is 1-based: the delay after the
 * first failure uses attempt=1 → baseDelay.
 */
export function nextDelayMs(
  attempt: number,
  policy: RetryPolicy,
  rng: () => number = Math.random,
): number {
  const raw = policy.baseDelayMs * policy.factor ** (attempt - 1);
  const capped = Math.min(raw, policy.maxDelayMs);
  return policy.jitter ? Math.floor(rng() * capped) : capped;
}

/** Load a retry policy from YAML, backfilling defaults. */
export function loadRetryPolicy(path: string): RetryPolicy {
  const doc = parse(readFileSync(path, "utf8")) as Partial<RetryPolicy> | null;
  return { ...DEFAULT_RETRY_POLICY, ...(doc ?? {}) };
}
