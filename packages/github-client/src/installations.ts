/** List GitHub App installations. */
import type { GhRest } from "./app.js";

export interface Installation {
  id: number;
  account: unknown;
}

export async function listInstallations(gh: GhRest): Promise<Installation[]> {
  const { data } = await gh.apps.listInstallations();
  return data.map((i) => ({ id: i.id, account: i.account }));
}
