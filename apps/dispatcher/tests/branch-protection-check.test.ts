import { describe, it, expect, vi } from "vitest";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import type { BranchProtectionSnapshot } from "@itpr/shared-types";
import type { GhRest } from "@itpr/github-client";
import {
  checkBranchProtection,
  evaluateRepoProtection,
  loadRequiredProtection,
  DEFAULT_REQUIRED,
} from "../src/repo-policy/branch-protection-check.js";
import { checkRepoSettings } from "../src/repo-policy/repo-settings-check.js";
import {
  buildProtectionRefusal,
  alreadyRefused,
  postRefusalOnce,
  REFUSAL_MARKER,
} from "../src/repo-policy/install-refusal.js";

const here = dirname(fileURLToPath(import.meta.url));
const POLICY = resolve(here, "../../../policies/branch-protection-required.yaml");

const REPO = { owner: "acme", repo: "widgets" };

const protectedSnap: BranchProtectionSnapshot = {
  branch: "main",
  requiresPullRequest: true,
  requiredApprovingReviews: 1,
  allowsForcePush: false,
  restrictsDirectPush: true,
  enforcesForAdmins: true,
};

describe("checkBranchProtection", () => {
  it("passes a fully protected branch", () => {
    expect(checkBranchProtection(protectedSnap, DEFAULT_REQUIRED)).toEqual({
      ok: true,
      missing: [],
    });
  });

  it("reports every missing rule on an unprotected branch", () => {
    const res = checkBranchProtection(
      {
        branch: "main",
        requiresPullRequest: false,
        requiredApprovingReviews: 0,
        allowsForcePush: true,
        restrictsDirectPush: false,
        enforcesForAdmins: false,
      },
      DEFAULT_REQUIRED,
    );
    expect(res.ok).toBe(false);
    expect(res.missing.length).toBe(4);
  });

  it("loads required rules from policy YAML", () => {
    const req = loadRequiredProtection(POLICY);
    expect(req.requirePullRequest).toBe(true);
    expect(req.minApprovals).toBeGreaterThanOrEqual(1);
  });
});

describe("evaluateRepoProtection", () => {
  it("treats an unprotected (404) branch as failing", async () => {
    const gh = {
      repos: {
        getBranchProtection: vi.fn().mockRejectedValue(new Error("Not Found")),
      },
    } as unknown as GhRest;
    const res = await evaluateRepoProtection(gh, { owner: "a", name: "b" }, "main", DEFAULT_REQUIRED);
    expect(res.ok).toBe(false);
  });
});

describe("checkRepoSettings", () => {
  it("flags Actions-can-approve", () => {
    expect(checkRepoSettings({ actionsCanApprovePullRequests: true }).ok).toBe(false);
    expect(checkRepoSettings({}).ok).toBe(true);
  });
});

describe("install-refusal", () => {
  it("builds a marked, idempotent refusal", () => {
    const msg = buildProtectionRefusal(["required pull request reviews"]);
    expect(msg).toContain(REFUSAL_MARKER);
    expect(alreadyRefused([msg])).toBe(true);
    expect(alreadyRefused(["hi"])).toBe(false);
  });

  it("posts once, skips when already refused", async () => {
    const createComment = vi.fn().mockResolvedValue({ data: { id: 1, html_url: "u" } });
    const gh = { issues: { createComment } } as unknown as GhRest;
    const skipped = await postRefusalOnce(gh, REPO, 1, "m", [`x ${REFUSAL_MARKER}`]);
    expect(skipped).toBeUndefined();
    expect(createComment).not.toHaveBeenCalled();
    const url = await postRefusalOnce(gh, REPO, 1, "m", []);
    expect(url).toBe("u");
  });
});
