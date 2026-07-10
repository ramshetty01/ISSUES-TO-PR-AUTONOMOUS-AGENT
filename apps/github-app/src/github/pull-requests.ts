/** Read pull request context (for pr_comment triggers). */
import { getPull, type GhRest, type Repo } from "@itpr/github-client";

export interface PullContext {
  number: number;
  state: string;
  merged: boolean;
}

export async function fetchPullContext(
  gh: GhRest,
  repo: Repo,
  prNumber: number,
): Promise<PullContext> {
  return getPull(gh, repo, prNumber);
}
