/** Pull request helpers. */
import type { GhRest, Repo } from "./app.js";

export interface CreatePullInput {
  title: string;
  head: string;
  base: string;
  body?: string;
}

export async function createPull(
  gh: GhRest,
  repo: Repo,
  input: CreatePullInput,
): Promise<{ number: number; url: string }> {
  const { data } = await gh.pulls.create({ ...repo, ...input });
  return { number: data.number, url: data.html_url };
}

export async function getPull(
  gh: GhRest,
  repo: Repo,
  prNumber: number,
): Promise<{ number: number; state: string; merged: boolean }> {
  const { data } = await gh.pulls.get({ ...repo, pull_number: prNumber });
  return { number: data.number, state: data.state, merged: data.merged };
}

export async function listPullFiles(
  gh: GhRest,
  repo: Repo,
  prNumber: number,
): Promise<Array<{ filename: string; status: string }>> {
  const { data } = await gh.pulls.listFiles({ ...repo, pull_number: prNumber });
  return data.map((f) => ({ filename: f.filename, status: f.status }));
}
