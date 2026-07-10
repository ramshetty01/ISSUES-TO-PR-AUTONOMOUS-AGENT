/**
 * Apply secret (and optionally PII) redaction to text. Idempotent: placeholders
 * never re-match, so redact(redact(x)) === redact(x).
 */
import { SECRET_PATTERNS, type RedactionPattern } from "./secret-patterns.js";
import { PII_PATTERNS } from "./pii-patterns.js";

export interface RedactOptions {
  /** Also scrub PII (emails, IPs, phone numbers). Default false. */
  pii?: boolean;
}

function applyPatterns(text: string, patterns: RedactionPattern[]): string {
  let out = text;
  for (const { regex, placeholder } of patterns) {
    // Clone with a fresh lastIndex so patterns are reusable + thread-safe.
    const re = new RegExp(regex.source, regex.flags);
    out = out.replace(re, placeholder);
  }
  return out;
}

/** Redact secrets from a string; optionally PII too. */
export function redact(text: string, opts: RedactOptions = {}): string {
  let out = applyPatterns(text, SECRET_PATTERNS);
  if (opts.pii) out = applyPatterns(out, PII_PATTERNS);
  return out;
}

/** True if the text contains at least one detectable secret. */
export function hasSecret(text: string): boolean {
  return SECRET_PATTERNS.some((p) =>
    new RegExp(p.regex.source, p.regex.flags).test(text),
  );
}

/**
 * Deep-redact a JSON-serializable value (strings redacted recursively). Useful
 * for scrubbing structured log records + trace payloads before they are stored.
 */
export function redactDeep<T>(value: T, opts: RedactOptions = {}): T {
  if (typeof value === "string") return redact(value, opts) as unknown as T;
  if (Array.isArray(value)) {
    return value.map((v) => redactDeep(v, opts)) as unknown as T;
  }
  if (value && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value)) out[k] = redactDeep(v, opts);
    return out as T;
  }
  return value;
}
