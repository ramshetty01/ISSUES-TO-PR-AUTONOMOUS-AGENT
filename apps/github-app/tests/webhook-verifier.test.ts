import { describe, it, expect } from "vitest";
import {
  computeSignature,
  verifySignature,
} from "../src/security/signature-check.js";
import { ReplayGuard } from "../src/security/replay-protection.js";
import { sanitizePayload } from "../src/security/payload-sanitizer.js";
import { WebhookVerifier } from "../src/github/webhook-verifier.js";

const SECRET = "whsec_test";

function body(obj: unknown): { raw: Buffer; parsed: unknown } {
  const raw = Buffer.from(JSON.stringify(obj));
  return { raw, parsed: obj };
}

describe("signature-check", () => {
  it("accepts a correct signature", () => {
    const { raw } = body({ action: "labeled" });
    const sig = computeSignature(SECRET, raw);
    expect(verifySignature(SECRET, raw, sig)).toBe(true);
  });

  it("rejects a tampered body", () => {
    const { raw } = body({ action: "labeled" });
    const sig = computeSignature(SECRET, raw);
    const tampered = Buffer.from(JSON.stringify({ action: "closed" }));
    expect(verifySignature(SECRET, tampered, sig)).toBe(false);
  });

  it("rejects a wrong secret", () => {
    const { raw } = body({ action: "labeled" });
    const sig = computeSignature("other", raw);
    expect(verifySignature(SECRET, raw, sig)).toBe(false);
  });

  it("rejects missing/malformed signatures", () => {
    const { raw } = body({});
    expect(verifySignature(SECRET, raw, undefined)).toBe(false);
    expect(verifySignature(SECRET, raw, "deadbeef")).toBe(false);
  });
});

describe("replay-protection", () => {
  it("accepts first delivery, rejects duplicate", () => {
    const guard = new ReplayGuard();
    expect(guard.check("d1")).toBe(true);
    expect(guard.check("d1")).toBe(false);
    expect(guard.check("d2")).toBe(true);
  });

  it("forgets ids after the TTL", () => {
    let t = 1000;
    const guard = new ReplayGuard({ ttlMs: 100, now: () => t });
    expect(guard.check("d1")).toBe(true);
    t += 200; // past TTL
    expect(guard.check("d1")).toBe(true); // evicted, treated as fresh
  });
});

describe("payload-sanitizer", () => {
  it("rejects oversized payloads", () => {
    const raw = Buffer.alloc(2048);
    const res = sanitizePayload(raw, {}, { maxBytes: 1024 });
    expect(res.ok).toBe(false);
  });

  it("rejects non-object payloads", () => {
    const raw = Buffer.from("[]");
    expect(sanitizePayload(raw, [], {}).ok).toBe(false);
    expect(sanitizePayload(Buffer.from("null"), null, {}).ok).toBe(false);
  });

  it("accepts a well-formed object", () => {
    const { raw, parsed } = body({ a: 1 });
    const res = sanitizePayload(raw, parsed, {});
    expect(res.ok).toBe(true);
  });
});

describe("WebhookVerifier (composed)", () => {
  const mk = () => new WebhookVerifier({ secret: SECRET });

  it("passes a valid, signed, first-time delivery", () => {
    const { raw, parsed } = body({ action: "labeled" });
    const out = mk().verify({
      rawBody: raw,
      parsed,
      signature: computeSignature(SECRET, raw),
      deliveryId: "d1",
    });
    expect(out.ok).toBe(true);
  });

  it("401 on bad signature", () => {
    const { raw, parsed } = body({ action: "labeled" });
    const out = mk().verify({
      rawBody: raw,
      parsed,
      signature: "sha256=bad",
      deliveryId: "d1",
    });
    expect(out).toMatchObject({ ok: false, status: 401 });
  });

  it("409 on replay", () => {
    const v = mk();
    const { raw, parsed } = body({ action: "labeled" });
    const input = {
      rawBody: raw,
      parsed,
      signature: computeSignature(SECRET, raw),
      deliveryId: "dup",
    };
    expect(v.verify(input).ok).toBe(true);
    expect(v.verify(input)).toMatchObject({ ok: false, status: 409 });
  });

  it("400 on missing delivery id", () => {
    const { raw, parsed } = body({});
    const out = mk().verify({
      rawBody: raw,
      parsed,
      signature: computeSignature(SECRET, raw),
      deliveryId: undefined,
    });
    expect(out).toMatchObject({ ok: false, status: 400 });
  });
});
