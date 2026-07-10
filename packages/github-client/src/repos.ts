/** Repository read helpers. */
import type { GhRest, Repo } from "./app.js";

export async function getRepo(
  gh: GhRest,
  repo: Repo,
): Promise<{ defaultBranch: string; private: boolean }> {
  const { data } = await gh.repos.get(repo);
  return { defaultBranch: data.default_branch, private: data.private };
}

export async function getDefaultBranch(gh: GhRest, repo: Repo): Promise<string> {
  return (await getRepo(gh, repo)).defaultBranch;
}
