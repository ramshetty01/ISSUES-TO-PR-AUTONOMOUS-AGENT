/**
 * Compose signature verification, replay protection, and payload sanitization
 * into a single guard run before any webhook handler.
 */
import { verifySignature } from "../security/signature-check.js";
import { ReplayGuard } from "../security/replay-protection.js";
import {
  sanitizePayload,
  type SanitizeOptions,
} from "../security/payload-sanitizer.js";

export interface VerifyInput {
  rawBody: Buffer;
  parsed: unknown;
  signature: string | undefined;
  deliveryId: string | undefined;
}

export type VerifyOutcome =
  | { ok: true; payload: Record<string, unknown> }
  | { ok: false; status: number; reason: string };

export interface WebhookVerifierOptions extends SanitizeOptions {
  secret: string;
  replayGuard?: ReplayGuard;
}

/** A reusable verifier bound to a secret + replay guard. */
export class WebhookVerifier {
  private readonly secret: string;
  private readonly replay: ReplayGuard;
  private readonly sanitizeOpts: SanitizeOptions;

  constructor(opts: WebhookVerifierOptions) {
    this.secret = opts.secret;
    this.replay = opts.replayGuard ?? new ReplayGuard();
    this.sanitizeOpts = opts.maxBytes !== undefined ? { maxBytes: opts.maxBytes } : {};
  }

  verify(input: VerifyInput): VerifyOutcome {
    if (!input.deliveryId) {
      return { ok: false, status: 400, reason: "missing delivery id" };
    }
    if (!verifySignature(this.secret, input.rawBody, input.signature)) {
      return { ok: false, status: 401, reason: "invalid signature" };
    }
    if (!this.replay.check(input.deliveryId)) {
      return { ok: false, status: 409, reason: "replayed delivery" };
    }
    const sanitized = sanitizePayload(input.rawBody, input.parsed, this.sanitizeOpts);
    if (!sanitized.ok) {
      return { ok: false, status: 400, reason: sanitized.reason };
    }
    return { ok: true, payload: sanitized.payload };
  }
}
