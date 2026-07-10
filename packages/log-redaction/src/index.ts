/** @itpr/log-redaction — secret + PII scrubbing for logs, traces, and artifacts. */
export {
  redact,
  redactDeep,
  hasSecret,
  type RedactOptions,
} from "./redact.js";
export { SECRET_PATTERNS, type RedactionPattern } from "./secret-patterns.js";
export { PII_PATTERNS } from "./pii-patterns.js";
export {
  POSITIVE_VECTORS,
  NEGATIVE_VECTORS,
  type Vector,
} from "./test-vectors.js";
