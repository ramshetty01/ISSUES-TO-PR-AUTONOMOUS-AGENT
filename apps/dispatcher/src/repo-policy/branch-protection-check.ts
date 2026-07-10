/**
 * Refuse to operate on repos whose default branch lacks required protection.
 * The agent only ever pushes to PR branches, so the default branch must require
 * PRs + reviews and disallow force/direct push.
 */
import { readFileSync } from "node:fs";
import { parse } from "yaml";
import type { BranchProtectionSnapshot, RepoRef } from "@itpr/shared-types";
import { getBranchProtectionSafe, type GhRest } from "@itpr/github-client";

export interface RequiredProtection {
  requirePullRequest: boolean;
  minApprovals: number;
  disallowForcePush: boolean;
  restrictDirectPush: boolean;
}

export interface ProtectionResult {
  ok: boolean;
  missing: string[];
}

/** Compare a snapshot against the required rules. */
export function checkBranchProtection(
  snap: BranchProtectionSnapshot,
  req: RequiredProtection,
): ProtectionResult {
  const missing: string[] = [];
  if (req.requirePullRequest && !snap.requiresPullRequest) {
    missing.push("required pull request reviews");
  }
  if (snap.requiredApprovingReviews < req.minApprovals) {
    missing.push(`at least ${req.minApprovals} approving review(s)`);
  }
  if (req.disallowForcePush && snap.allowsForcePush) {
    missing.push("force pushes must be disabled");
  }
  if (req.restrictDirectPush && !snap.restrictsDirectPush) {
    missing.push("direct pushes to the default branch must be restricted");
  }
  return { ok: missing.length === 0, missing };
}

/** Fetch protection for a branch and evaluate it (unprotected → fails). */
export async function evaluateRepoProtection(
  gh: GhRest,
  repo: RepoRef,
  branch: string,
  req: RequiredProtection,
): Promise<ProtectionResult> {
  const snap = await getBranchProtectionSafe(
    gh,
    { owner: repo.owner, repo: repo.name },
    branch,
  );
  return checkBranchProtection(snap, req);
}

interface RequiredFile {
  requirePullRequest?: boolean;
  minApprovals?: number;
  disallowForcePush?: boolean;
  restrictDirectPush?: boolean;
}

export const DEFAULT_REQUIRED: RequiredProtection = {
  requirePullRequest: true,
  minApprovals: 1,
  disallowForcePush: true,
  restrictDirectPush: true,
};

/** Load required protection rules from policy YAML. */
export function loadRequiredProtection(path: string): RequiredProtection {
  const doc = parse(readFileSync(path, "utf8")) as RequiredFile | null;
  if (!doc) return DEFAULT_REQUIRED;
  return {
    requirePullRequest: doc.requirePullRequest ?? DEFAULT_REQUIRED.requirePullRequest,
    minApprovals: doc.minApprovals ?? DEFAULT_REQUIRED.minApprovals,
    disallowForcePush: doc.disallowForcePush ?? DEFAULT_REQUIRED.disallowForcePush,
    restrictDirectPush: doc.restrictDirectPush ?? DEFAULT_REQUIRED.restrictDirectPush,
  };
}
