import { describe, it, expect } from "vitest";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import {
  matchesTriggerLabel,
  triggerLabel,
  loadAllowedLabels,
} from "../src/filters/label-filter.js";
import { isAllowedRepo } from "../src/filters/repo-allowlist.js";
import { isAllowedActor } from "../src/filters/actor-filter.js";
import type { Actor, AllowlistEntry } from "@itpr/shared-types";

const here = dirname(fileURLToPath(import.meta.url));
const POLICY = resolve(here, "../../../policies/allowed-labels.yaml");

describe("label-filter", () => {
  it("matches only allowed trigger labels", () => {
    expect(matchesTriggerLabel(["bug", "agent-fix"], ["agent-fix"])).toBe(true);
    expect(matchesTriggerLabel(["bug", "wontfix"], ["agent-fix"])).toBe(false);
  });

  it("returns the specific triggering label", () => {
    expect(triggerLabel(["bug", "agent-fix"], ["agent-fix"])).toBe("agent-fix");
    expect(triggerLabel(["bug"], ["agent-fix"])).toBeUndefined();
  });

  it("loads allowed labels from the policy YAML", () => {
    expect(loadAllowedLabels(POLICY)).toContain("agent-fix");
  });
});

describe("repo-allowlist (deny by default)", () => {
  const allow: AllowlistEntry[] = [
    { owner: "acme", name: "widgets" },
    { owner: "globex", name: "*" },
  ];

  it("allows an exact match", () => {
    expect(isAllowedRepo({ owner: "acme", name: "widgets" }, allow)).toBe(true);
  });

  it("allows a wildcard owner", () => {
    expect(isAllowedRepo({ owner: "globex", name: "anything" }, allow)).toBe(true);
  });

  it("denies everything else", () => {
    expect(isAllowedRepo({ owner: "acme", name: "other" }, allow)).toBe(false);
    expect(isAllowedRepo({ owner: "evil", name: "repo" }, allow)).toBe(false);
    expect(isAllowedRepo({ owner: "acme", name: "widgets" }, [])).toBe(false);
  });
});

describe("actor-filter", () => {
  const user = (login: string): Actor => ({ login, type: "User" });

  it("rejects bots", () => {
    expect(isAllowedActor({ login: "dependabot", type: "Bot" })).toBe(false);
  });

  it("rejects ignored logins (self)", () => {
    expect(isAllowedActor(user("itpr-bot"), { ignoreLogins: ["itpr-bot"] })).toBe(false);
  });

  it("permits any non-bot when no allowlist set", () => {
    expect(isAllowedActor(user("alice"))).toBe(true);
  });

  it("restricts to allowLogins when set", () => {
    expect(isAllowedActor(user("alice"), { allowLogins: ["bob"] })).toBe(false);
    expect(isAllowedActor(user("bob"), { allowLogins: ["bob"] })).toBe(true);
  });
});
