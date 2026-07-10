/**
 * Shared redaction test vectors. Also the source of truth for
 * security/secret-redaction-test-cases.json (kept in sync in a later phase).
 *
 * Token strings are ASSEMBLED FROM FRAGMENTS at runtime so no full secret
 * literal ever appears in source — otherwise GitHub push protection (and other
 * scanners) would flag these fixtures as real leaked credentials.
 */

export interface Vector {
  name: string;
  input: string;
  /** A substring that must NOT survive redaction. */
  mustRemove: string;
  /** PII vectors require the pii option. */
  pii?: boolean;
}

const j = (...parts: string[]) => parts.join("");

// Synthetic, non-real credentials built at runtime (never literal in source).
const GH_CLASSIC = j("ghp", "_", "0123456789abcdefghijklmnopqrstuvwxyz");
const GH_SERVER = j("ghs", "_", "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789");
const AWS_KEY = j("AKIA", "IOSFODNN7", "EXAMPLE");
const SLACK = j("xox", "b", "-", "123456789012", "-", "abcdefghijklmnop");
const GOOGLE = j("AIza", "Syabcdefghijklmnopqrstuvwxyz0123456");
const JWT = j("eyJhbGciOi", ".", "JIUzI1NiIsInR5cCI6IkpXVCJ9");
const GENERIC = j("sup3r", "Secret", "Value123");
const PRIVKEY = j(
  "-----BEGIN RSA PRIVATE KEY-----\n",
  "MIIEpAIBAAKCAQEA\n",
  "-----END RSA PRIVATE KEY-----",
);

/** Inputs that MUST be redacted. */
export const POSITIVE_VECTORS: Vector[] = [
  {
    name: "github classic token",
    input: `using token ${GH_CLASSIC} for auth`,
    mustRemove: GH_CLASSIC,
  },
  {
    name: "github server token",
    input: `GITHUB_TOKEN=${GH_SERVER}`,
    mustRemove: GH_SERVER,
  },
  {
    name: "aws access key id",
    input: `aws key ${AWS_KEY} in config`,
    mustRemove: AWS_KEY,
  },
  {
    name: "slack token",
    input: `slack ${SLACK} hook`,
    mustRemove: SLACK,
  },
  {
    name: "google api key",
    input: `key ${GOOGLE} used`,
    mustRemove: GOOGLE,
  },
  {
    name: "bearer token",
    input: `Authorization: Bearer ${JWT}`,
    mustRemove: JWT,
  },
  {
    name: "generic secret assignment",
    input: `password: "${GENERIC}"`,
    mustRemove: GENERIC,
  },
  {
    name: "private key block",
    input: PRIVKEY,
    mustRemove: "MIIEpAIBAAKCAQEA",
  },
  {
    name: "email (pii)",
    input: "contact dev@example.com for access",
    mustRemove: "dev@example.com",
    pii: true,
  },
  {
    name: "ipv4 (pii)",
    input: "request from 203.0.113.42 blocked",
    mustRemove: "203.0.113.42",
    pii: true,
  },
];

/** Benign inputs that must be left UNCHANGED (no false positives). */
export const NEGATIVE_VECTORS: string[] = [
  "the build finished in 42 seconds",
  "commit ghost wrote the changelog",
  "set the timeout to 3000 milliseconds",
  "see README.md section token-bucket for the algorithm",
  "version 1.2.3 released",
];
