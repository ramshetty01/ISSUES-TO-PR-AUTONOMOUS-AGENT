import { afterEach, describe, expect, it, vi } from "vitest";

import { logger } from "../src/logging/logger.js";

// Fake token assembled from fragments so no literal secret appears in source.
const GH_TOKEN = ["ghp", "_", "0123456789abcdefghijklmnopqrstuvwxyz"].join("");

describe("app logger redaction", () => {
  afterEach(() => vi.restoreAllMocks());

  it("scrubs secrets from a field before writing to stdout", () => {
    const spy = vi.spyOn(console, "log").mockImplementation(() => {});
    logger.info("token refreshed", { token: GH_TOKEN });
    const line = spy.mock.calls[0]?.[0] as string;
    expect(line).not.toContain(GH_TOKEN);
    expect(line).toContain("[REDACTED");
  });

  it("scrubs secrets from the message on the error stream", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    logger.error(`auth failed with ${GH_TOKEN}`);
    const line = spy.mock.calls[0]?.[0] as string;
    expect(line).not.toContain(GH_TOKEN);
  });
});
