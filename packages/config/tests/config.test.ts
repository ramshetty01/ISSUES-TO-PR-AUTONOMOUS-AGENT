import { describe, it, expect } from "vitest";
import { loadConfig, ConfigError } from "../src/index.js";

/** Minimal valid source: only the real secrets; dev defaults backfill the rest. */
const validSecrets = {
  GITHUB_APP_ID: "123456",
  GITHUB_APP_PRIVATE_KEY: "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----",
  GITHUB_WEBHOOK_SECRET: "whsec_test",
};

describe("loadConfig", () => {
  it("parses a valid env, backfilling dev defaults", () => {
    const cfg = loadConfig({ ...validSecrets, NODE_ENV: "development" });
    expect(cfg.GITHUB_APP_ID).toBe("123456");
    expect(cfg.AWS_ENDPOINT_URL).toBe("http://localhost:4566");
    expect(cfg.PORT).toBe(3001);
    expect(cfg.LANGFUSE_HOST).toBe("http://localhost:3000");
  });

  it("coerces PORT to a number and splits provider order", () => {
    const cfg = loadConfig({
      ...validSecrets,
      PORT: "8080",
      LLM_PROVIDER_ORDER: "openrouter, groq ,mock",
      OPENROUTER_MODEL: "tencent/hy3:free",
      NVIDIA_NIM_MODEL: "qwen/qwen3.5-122b-a10b",
    });
    expect(cfg.PORT).toBe(8080);
    expect(cfg.LLM_PROVIDER_ORDER).toEqual(["openrouter", "groq", "mock"]);
    expect(cfg.OPENROUTER_MODEL).toBe("tencent/hy3:free");
    expect(cfg.NVIDIA_NIM_MODEL).toBe("qwen/qwen3.5-122b-a10b");
  });

  it("normalizes escaped private-key newlines from .env files", () => {
    const cfg = loadConfig({
      ...validSecrets,
      GITHUB_APP_PRIVATE_KEY: "-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----\\n",
    });
    expect(cfg.GITHUB_APP_PRIVATE_KEY).toBe(
      "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\n",
    );
  });

  it("rejects a missing required secret with a clear, aggregated message", () => {
    let err: unknown;
    try {
      loadConfig({ NODE_ENV: "development" });
    } catch (e) {
      err = e;
    }
    expect(err).toBeInstanceOf(ConfigError);
    const ce = err as ConfigError;
    expect(ce.issues.some((i) => i.includes("GITHUB_APP_ID"))).toBe(true);
    expect(ce.issues.some((i) => i.includes("GITHUB_WEBHOOK_SECRET"))).toBe(true);
  });

  it("in production does NOT backfill defaults (missing infra keys fail)", () => {
    expect(() =>
      loadConfig({ ...validSecrets, NODE_ENV: "production" }),
    ).toThrow(ConfigError);
  });

  it("rejects an invalid URL", () => {
    expect(() =>
      loadConfig({ ...validSecrets, AWS_ENDPOINT_URL: "not-a-url" }),
    ).toThrow(ConfigError);
  });
});
