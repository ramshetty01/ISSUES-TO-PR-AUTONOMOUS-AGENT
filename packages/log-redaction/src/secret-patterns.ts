/**
 * Secret detection patterns. Each produces a named placeholder so redaction is
 * traceable and idempotent (placeholders never re-match a pattern).
 */

export interface RedactionPattern {
  name: string;
  regex: RegExp;
  /** Placeholder inserted in place of the match. */
  placeholder: string;
}

/** Standard placeholder for a named secret. */
const ph = (name: string) => `[REDACTED:${name}]`;

/**
 * Order matters: multi-line blocks (private keys) run before line-scoped
 * patterns. All regexes are global; `redact` resets lastIndex per use.
 */
export const SECRET_PATTERNS: RedactionPattern[] = [
  {
    name: "private_key",
    regex:
      /-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z]+ )?PRIVATE KEY-----/g,
    placeholder: ph("private_key"),
  },
  {
    // ghp_, gho_, ghu_, ghs_, ghr_ classic tokens (40 chars total)
    name: "github_token",
    regex: /\bgh[opusr]_[A-Za-z0-9]{36}\b/g,
    placeholder: ph("github_token"),
  },
  {
    name: "github_pat",
    regex: /\bgithub_pat_[A-Za-z0-9_]{60,}\b/g,
    placeholder: ph("github_pat"),
  },
  {
    name: "aws_access_key_id",
    regex: /\b(?:AKIA|ASIA)[0-9A-Z]{16}\b/g,
    placeholder: ph("aws_access_key_id"),
  },
  {
    name: "slack_token",
    regex: /\bxox[baprs]-[A-Za-z0-9-]{10,}\b/g,
    placeholder: ph("slack_token"),
  },
  {
    name: "google_api_key",
    regex: /\bAIza[0-9A-Za-z_\-]{35}\b/g,
    placeholder: ph("google_api_key"),
  },
  {
    name: "bearer_token",
    regex: /\bBearer\s+[A-Za-z0-9._~+/\-]{10,}=*/g,
    placeholder: `Bearer ${ph("bearer_token")}`,
  },
  {
    // key/secret/token/password assignments: redact the value, keep the key name
    name: "generic_secret",
    regex:
      /\b(api[_-]?key|secret|token|password|passwd|access[_-]?key)\b(\s*[:=]\s*)(['"]?)[A-Za-z0-9._\-]{12,}\3/gi,
    placeholder: `$1$2$3${ph("generic_secret")}$3`,
  },
];
