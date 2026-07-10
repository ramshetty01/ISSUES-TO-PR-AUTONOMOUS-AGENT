/** Read issue context for a triggered event. */
import { getIssue, type GhRest, type Repo, type IssueDetail } from "@itpr/github-client";

export interface IssueContext extends IssueDetail {
  number: number;
}

export async function fetchIssueContext(
  gh: GhRest,
  repo: Repo,
  issueNumber: number,
): Promise<IssueContext> {
  const detail = await getIssue(gh, repo, issueNumber);
  return { number: issueNumber, ...detail };
}
