/**
 * Build (and optionally post) a refusal explaining the repo-policy failure.
 * The message is idempotent via a hidden marker so we never spam an issue.
 */
import { createIssueComment, type GhRest, type Repo } from "@itpr/github-client";

export const REFUSAL_MARKER = "<!-- itpr:policy-refusal -->";

/** Build a branch-protection refusal message. */
export function buildProtectionRefusal(missing: string[]): string {
  return [
    "The agent will not run on this repository yet.",
    "",
    "The default branch is missing required protection:",
    ...missing.map((m) => `- ${m}`),
    "",
    "Enable these in **Settings → Branches**, then re-trigger.",
    "",
    REFUSAL_MARKER,
  ].join("\n");
}

/** Build a repo-settings refusal message. */
export function buildSettingsRefusal(issues: string[]): string {
  return [
    "The agent will not run on this repository due to unsafe settings:",
    ...issues.map((i) => `- ${i}`),
    "",
    REFUSAL_MARKER,
  ].join("\n");
}

/** True if a prior refusal already exists among the given comment bodies. */
export function alreadyRefused(existingBodies: string[]): boolean {
  return existingBodies.some((b) => b.includes(REFUSAL_MARKER));
}

/** Post a refusal once; returns the url, or undefined if already refused. */
export async function postRefusalOnce(
  gh: GhRest,
  repo: Repo,
  issueNumber: number,
  message: string,
  existingBodies: string[],
): Promise<string | undefined> {
  if (alreadyRefused(existingBodies)) return undefined;
  const { url } = await createIssueComment(gh, repo, issueNumber, message);
  return url;
}
