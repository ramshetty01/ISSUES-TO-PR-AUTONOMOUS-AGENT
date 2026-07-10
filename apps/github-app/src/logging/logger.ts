/**
 * Minimal structured JSON logger. Emits one line per event, enriched with the
 * current request context. Every line is passed through log-redaction so a
 * secret in a message or field can never reach stdout.
 */
import { redact } from "@itpr/log-redaction";

import { currentContext } from "./request-context.js";

export type Level = "debug" | "info" | "warn" | "error";

function emit(level: Level, msg: string, fields?: Record<string, unknown>): void {
  const ctx = currentContext();
  const record = {
    ts: new Date().toISOString(),
    level,
    msg,
    ...(ctx ? { requestId: ctx.requestId, deliveryId: ctx.deliveryId, event: ctx.event } : {}),
    ...fields,
  };
  const line = redact(JSON.stringify(record));
  if (level === "error" || level === "warn") console.error(line);
  else console.log(line);
}

export const logger = {
  debug: (msg: string, fields?: Record<string, unknown>) => emit("debug", msg, fields),
  info: (msg: string, fields?: Record<string, unknown>) => emit("info", msg, fields),
  warn: (msg: string, fields?: Record<string, unknown>) => emit("warn", msg, fields),
  error: (msg: string, fields?: Record<string, unknown>) => emit("error", msg, fields),
};
