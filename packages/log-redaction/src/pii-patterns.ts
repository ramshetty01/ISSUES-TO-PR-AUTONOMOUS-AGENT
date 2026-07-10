/**
 * PII detection patterns. Applied only when redaction is asked to scrub PII
 * (opt-in), since IPs/emails are often legitimate in logs.
 */
import type { RedactionPattern } from "./secret-patterns.js";

const ph = (name: string) => `[REDACTED:${name}]`;

export const PII_PATTERNS: RedactionPattern[] = [
  {
    name: "email",
    regex: /\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b/g,
    placeholder: ph("email"),
  },
  {
    name: "ipv4",
    regex: /\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b/g,
    placeholder: ph("ipv4"),
  },
  {
    name: "phone",
    regex:
      /(?<!\d)(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)/g,
    placeholder: ph("phone"),
  },
];
