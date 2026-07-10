/** Read branch-protection rules and map them to a shared-types snapshot. */
import type { BranchProtectionSnapshot } from "@itpr/shared-types";
import type { GhRest, Repo } from "./app.js";

/**
 * Fetch branch protection and normalize to a BranchProtectionSnapshot.
 * When a branch is unprotected, GitHub returns 404; callers treat a thrown
 * error as "no protection" via `getBranchProtectionSafe`.
 */
export async function getBranchProtection(
  gh: GhRest,
  repo: Repo,
  branch: string,
): Promise<BranchProtectionSnapshot> {
  const { data } = await gh.repos.getBranchProtection({ ...repo, branch });
  return {
    branch,
    requiresPullRequest: data.required_pull_request_reviews != null,
    requiredApprovingReviews:
      data.required_pull_request_reviews?.required_approving_review_count ?? 0,
    allowsForcePush: data.allow_force_pushes?.enabled ?? false,
    restrictsDirectPush: data.restrictions != null,
    enforcesForAdmins: data.enforce_admins?.enabled ?? false,
  };
}

/** Like getBranchProtection but returns an unprotected snapshot on 404/error. */
export async function getBranchProtectionSafe(
  gh: GhRest,
  repo: Repo,
  branch: string,
): Promise<BranchProtectionSnapshot> {
  try {
    return await getBranchProtection(gh, repo, branch);
  } catch {
    return {
      branch,
      requiresPullRequest: false,
      requiredApprovingReviews: 0,
      allowsForcePush: true,
      restrictsDirectPush: false,
      enforcesForAdmins: false,
    };
  }
}
