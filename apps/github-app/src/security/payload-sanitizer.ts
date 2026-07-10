/**
 * Guard against oversized or malformed webhook payloads before they reach a
 * handler. GitHub caps deliveries at 25 MB; we enforce a tighter default.
 */

export interface SanitizeOptions {
  /** Max accepted raw body size in bytes. Default 1 MiB. */
  maxBytes?: number;
}

export type SanitizeResult =
  | { ok: true; payload: Record<string, unknown> }
  | { ok: false; reason: string };

const DEFAULT_MAX = 1024 * 1024;

/** Validate size + basic shape (must be a JSON object). */
export function sanitizePayload(
  rawBody: Buffer,
  parsed: unknown,
  opts: SanitizeOptions = {},
): SanitizeResult {
  const maxBytes = opts.maxBytes ?? DEFAULT_MAX;
  if (rawBody.length > maxBytes) {
    return { ok: false, reason: `payload too large (${rawBody.length} > ${maxBytes})` };
  }
  if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
    return { ok: false, reason: "payload is not a JSON object" };
  }
  return { ok: true, payload: parsed as Record<string, unknown> };
}
