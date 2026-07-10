/** Issue read + comment helpers. */
import type { GhRest, Repo } from "./app.js";

export interface IssueDetail {
  title: string;
  body: string | null;
  state: string;
}

export async function getIssue(
  gh: GhRest,
  repo: Repo,
  issueNumber: number,
): Promise<IssueDetail> {
  const { data } = await gh.issues.get({ ...repo, issue_number: issueNumber });
  return { title: data.title, body: data.body, state: data.state };
}

export async function createIssueComment(
  gh: GhRest,
  repo: Repo,
  issueNumber: number,
  body: string,
): Promise<{ id: number; url: string }> {
  const { data } = await gh.issues.createComment({
    ...repo,
    issue_number: issueNumber,
    body,
  });
  return { id: data.id, url: data.html_url };
}
