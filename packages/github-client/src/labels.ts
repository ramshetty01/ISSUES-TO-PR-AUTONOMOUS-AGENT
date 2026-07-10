/** Issue/PR label helpers. */
import type { GhRest, Repo } from "./app.js";

export async function addLabels(
  gh: GhRest,
  repo: Repo,
  issueNumber: number,
  labels: string[],
): Promise<void> {
  await gh.issues.addLabels({ ...repo, issue_number: issueNumber, labels });
}

export async function removeLabel(
  gh: GhRest,
  repo: Repo,
  issueNumber: number,
  name: string,
): Promise<void> {
  await gh.issues.removeLabel({ ...repo, issue_number: issueNumber, name });
}

export async function listLabels(
  gh: GhRest,
  repo: Repo,
  issueNumber: number,
): Promise<string[]> {
  const { data } = await gh.issues.listLabelsOnIssue({
    ...repo,
    issue_number: issueNumber,
  });
  return data.map((l) => l.name);
}
