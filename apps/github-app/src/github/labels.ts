/** Apply/read labels in response to events. */
import { addLabels, listLabels, type GhRest, type Repo } from "@itpr/github-client";

export async function applyLabels(
  gh: GhRest,
  repo: Repo,
  issueNumber: number,
  labels: string[],
): Promise<void> {
  if (labels.length === 0) return;
  await addLabels(gh, repo, issueNumber, labels);
}

export async function currentLabels(
  gh: GhRest,
  repo: Repo,
  issueNumber: number,
): Promise<string[]> {
  return listLabels(gh, repo, issueNumber);
}
