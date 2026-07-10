/** Minimal span helper. Wraps an async op, recording duration + outcome. */
import { logger } from "../logging/logger.js";

export interface Span {
  end(outcome: "ok" | "error", fields?: Record<string, unknown>): void;
}

export function startSpan(name: string, fields?: Record<string, unknown>): Span {
  const start = Date.now();
  return {
    end(outcome, endFields) {
      logger.debug("span", {
        span: name,
        outcome,
        durationMs: Date.now() - start,
        ...fields,
        ...endFields,
      });
    },
  };
}
