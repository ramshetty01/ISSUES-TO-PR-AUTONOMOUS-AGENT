/** Git ref helpers (branches live under refs/heads/*). */
import type { GhRest, Repo } from "./app.js";

/** Read the sha a ref points at. `ref` is e.g. "heads/main". */
export async function getRef(
  gh: GhRest,
  repo: Repo,
  ref: string,
): Promise<string> {
  const { data } = await gh.git.getRef({ ...repo, ref });
  return data.object.sha;
}

/** Create a new branch ref. `branch` is the short name (no refs/heads prefix). */
export async function createBranch(
  gh: GhRest,
  repo: Repo,
  branch: string,
  sha: string,
): Promise<string> {
  const { data } = await gh.git.createRef({
    ...repo,
    ref: `refs/heads/${branch}`,
    sha,
  });
  return data.ref;
}

/** Update a branch ref. Force is refused by callers on protected branches. */
export async function updateBranch(
  gh: GhRest,
  repo: Repo,
  branch: string,
  sha: string,
  force = false,
): Promise<string> {
  const { data } = await gh.git.updateRef({
    ...repo,
    ref: `heads/${branch}`,
    sha,
    force,
  });
  return data.ref;
}
