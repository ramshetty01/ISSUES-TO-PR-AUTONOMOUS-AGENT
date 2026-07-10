/**
 * Verify the GitHub webhook HMAC signature (X-Hub-Signature-256) against the
 * raw request body. Uses a constant-time comparison to avoid timing leaks.
 */
import { createHmac, timingSafeEqual } from "node:crypto";

/** Compute the expected `sha256=...` signature for a body. */
export function computeSignature(secret: string, rawBody: Buffer | string): string {
  const hmac = createHmac("sha256", secret);
  hmac.update(rawBody);
  return `sha256=${hmac.digest("hex")}`;
}

/**
 * Constant-time check of a received signature. Returns false (never throws) for
 * missing/malformed signatures.
 */
export function verifySignature(
  secret: string,
  rawBody: Buffer | string,
  signature: string | undefined,
): boolean {
  if (!signature || !signature.startsWith("sha256=")) return false;
  const expected = computeSignature(secret, rawBody);
  const a = Buffer.from(expected);
  const b = Buffer.from(signature);
  // Length check first: timingSafeEqual throws on length mismatch.
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}
