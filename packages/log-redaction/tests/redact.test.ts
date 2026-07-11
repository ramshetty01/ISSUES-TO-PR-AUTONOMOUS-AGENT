import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import {
  redact,
  redactDeep,
  hasSecret,
  POSITIVE_VECTORS,
  NEGATIVE_VECTORS,
} from "../src/index.js";

interface SecurityVector {
  name: string;
  inputParts: string[];
  expectedRedacted: string;
}

function loadSecurityVectors(): SecurityVector[] {
  const path = resolve(process.cwd(), "../../security/secret-redaction-test-cases.json");
  const parsed = JSON.parse(readFileSync(path, "utf8")) as { cases: SecurityVector[] };
  return parsed.cases;
}

describe("redact — positive vectors", () => {
  for (const v of POSITIVE_VECTORS) {
    it(`redacts ${v.name}`, () => {
      const out = redact(v.input, { pii: v.pii ?? false });
      expect(out).not.toContain(v.mustRemove);
      expect(out).toContain("[REDACTED:");
    });
  }
});

describe("redact — negative vectors (no false positives)", () => {
  for (const s of NEGATIVE_VECTORS) {
    it(`leaves benign text unchanged: "${s.slice(0, 24)}..."`, () => {
      expect(redact(s, { pii: true })).toBe(s);
    });
  }
});

describe("redact — security fixture vectors", () => {
  for (const v of loadSecurityVectors()) {
    it(`matches security fixture: ${v.name}`, () => {
      expect(redact(v.inputParts.join(""))).toBe(v.expectedRedacted);
    });
  }
});

// Assembled from fragments so no full token literal appears in source
// (avoids tripping secret scanners / push protection on test fixtures).
const j = (...p: string[]) => p.join("");
const GHP = j("ghp", "_", "0123456789abcdefghijklmnopqrstuvwxyz");
const GHS = j("ghs", "_", "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789");
const JWT = j("eyJhbGciOi", ".", "JIUzI1NiIsInR5cCI6IkpXVCJ9");

describe("redact — properties", () => {
  it("is idempotent", () => {
    const input = `token ${GHP} and dev@example.com`;
    const once = redact(input, { pii: true });
    const twice = redact(once, { pii: true });
    expect(twice).toBe(once);
  });

  it("does not scrub PII unless asked", () => {
    const out = redact("email dev@example.com", {});
    expect(out).toContain("dev@example.com");
  });

  it("hasSecret detects tokens but not prose", () => {
    expect(hasSecret(GHP)).toBe(true);
    expect(hasSecret("just a normal log line")).toBe(false);
  });

  it("redactDeep scrubs nested structures", () => {
    const record = {
      msg: "auth ok",
      headers: { authorization: `Bearer ${JWT}` },
      tokens: [GHS],
      count: 3,
    };
    const out = redactDeep(record);
    expect(JSON.stringify(out)).not.toContain("eyJhbGciOi");
    expect(JSON.stringify(out)).not.toContain(GHS);
    expect(out.count).toBe(3);
  });
});
