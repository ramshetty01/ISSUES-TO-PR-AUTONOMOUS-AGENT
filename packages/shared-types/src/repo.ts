/**
 * Repository identity, policy, and branch-protection types.
 * Consumed by github-app filters, dispatcher repo-policy gate, and the worker.
 */

/** Minimal repository reference (owner + name). */
export interface RepoRef {
  owner: string;
  name: string;
}

/** An entry in the repo allowlist. Deny-by-default: only listed repos are processed. */
export interface AllowlistEntry {
  owner: string;
  /** Repo name, or "*" to allow all repos under the owner. */
  name: string;
}

/** Per-repo operating policy resolved from policies/default-repo-policy.yaml. */
export interface RepoPolicy {
  repo: RepoRef;
  /** Labels that trigger the agent (e.g. ["agent-fix"]). */
  requiredLabels: string[];
  /** Maximum number of changed lines allowed in a single PR. */
  maxDiffLines: number;
  /** Maximum number of files a single PR may touch. */
  maxChangedFiles: number;
  /** Whether the repo has passed the branch-protection gate. */
  branchProtectionOk: boolean;
}

/** Snapshot of a branch's protection rules, read via the GitHub API. */
export interface BranchProtectionSnapshot {
  branch: string;
  requiresPullRequest: boolean;
  requiredApprovingReviews: number;
  allowsForcePush: boolean;
  restrictsDirectPush: boolean;
  enforcesForAdmins: boolean;
}
