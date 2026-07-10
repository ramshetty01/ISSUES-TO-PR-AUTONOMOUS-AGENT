import { describe, it, expect } from "vitest";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import {
  shouldRetry,
  nextDelayMs,
  loadRetryPolicy,
  DEFAULT_RETRY_POLICY,
  type RetryPolicy,
} from "../src/repo-policy/retry-policy.js";

const here = dirname(fileURLToPath(import.meta.url));
const POLICY = resolve(here, "../../../policies/retry-policy.yaml");

const p: RetryPolicy = {
  maxAttempts: 4,
  baseDelayMs: 100,
  maxDelayMs: 1000,
  factor: 2,
};

describe("shouldRetry", () => {
  it("retries below maxAttempts, stops at/after it", () => {
    expect(shouldRetry(1, p)).toBe(true);
    expect(shouldRetry(3, p)).toBe(true);
    expect(shouldRetry(4, p)).toBe(false);
  });
});

describe("nextDelayMs", () => {
  it("grows exponentially from the base", () => {
    expect(nextDelayMs(1, p)).toBe(100);
    expect(nextDelayMs(2, p)).toBe(200);
    expect(nextDelayMs(3, p)).toBe(400);
  });

  it("caps at maxDelayMs", () => {
    expect(nextDelayMs(10, p)).toBe(1000);
  });

  it("applies full jitter within [0, delay] when enabled", () => {
    const jp = { ...p, jitter: true };
    const d = nextDelayMs(3, jp, () => 0.5);
    expect(d).toBe(200); // 0.5 * 400
  });
});

describe("loadRetryPolicy", () => {
  it("loads from YAML backfilling defaults", () => {
    const loaded = loadRetryPolicy(POLICY);
    expect(loaded.maxAttempts).toBe(DEFAULT_RETRY_POLICY.maxAttempts);
    expect(loaded.factor).toBe(2);
  });
});
