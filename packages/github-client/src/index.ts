/** @itpr/github-client — App auth + typed GitHub REST helpers over a mockable GhRest. */
export { createApp, type GhRest, type Repo, type BranchProtectionApi } from "./app.js";
export {
  getInstallationToken,
  installationClient,
  getInstallationPermissions,
  type InstallationToken,
  type PermissionLevel,
} from "./auth.js";
export { listInstallations, type Installation } from "./installations.js";
export { getRepo, getDefaultBranch } from "./repos.js";
export { getIssue, createIssueComment, type IssueDetail } from "./issues.js";
export {
  createPull,
  getPull,
  listPullFiles,
  type CreatePullInput,
} from "./pulls.js";
export { getRef, createBranch, updateBranch } from "./refs.js";
export { addLabels, removeLabel, listLabels } from "./labels.js";
export { getBranchProtection, getBranchProtectionSafe } from "./protection.js";
