/**
 * Refuse repos with unsafe settings — notably, letting GitHub Actions approve
 * pull requests would defeat the required-review gate.
 */

export interface RepoSettings {
  /** Whether Actions/bots can approve PRs (should be false). */
  actionsCanApprovePullRequests?: boolean;
  /** Whether the default branch allows auto-merge without review. */
  allowsUnreviewedAutoMerge?: boolean;
}

export interface SettingsResult {
  ok: boolean;
  issues: string[];
}

export function checkRepoSettings(settings: RepoSettings): SettingsResult {
  const issues: string[] = [];
  if (settings.actionsCanApprovePullRequests) {
    issues.push("GitHub Actions is allowed to approve pull requests");
  }
  if (settings.allowsUnreviewedAutoMerge) {
    issues.push("auto-merge is allowed without a required review");
  }
  return { ok: issues.length === 0, issues };
}
