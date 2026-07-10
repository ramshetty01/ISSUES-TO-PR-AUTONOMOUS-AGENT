/**
 * Installation-scoped authentication: mint short-lived installation tokens and
 * produce an installation-authenticated REST client.
 */
import type { App } from "@octokit/app";
import { Octokit } from "@octokit/rest";
import type { GhRest } from "./app.js";

export interface InstallationToken {
  token: string;
  /** ISO-8601 expiry. */
  expiresAt: string;
}

/** Mint a short-lived installation access token. */
export async function getInstallationToken(
  app: App,
  installationId: number,
): Promise<InstallationToken> {
  const octokit = await app.getInstallationOctokit(installationId);
  const { token, expiresAt } = (await octokit.auth({
    type: "installation",
  })) as { token: string; expiresAt: string };
  return { token, expiresAt };
}

/** Get a REST client authenticated as the installation. */
export async function installationClient(
  app: App,
  installationId: number,
): Promise<GhRest> {
  const { token } = await getInstallationToken(app, installationId);
  // @octokit/rest's Octokit exposes the full REST surface under `.rest`,
  // which structurally satisfies our GhRest subset.
  return new Octokit({ auth: token }).rest as unknown as GhRest;
}

/** Access levels a GitHub App installation can grant per scope. */
export type PermissionLevel = "read" | "write" | "admin";

/** Fetch the permissions granted to an installation (scope -> level). */
export async function getInstallationPermissions(
  app: App,
  installationId: number,
): Promise<Record<string, PermissionLevel>> {
  const res = await app.octokit.request(
    "GET /app/installations/{installation_id}",
    { installation_id: installationId },
  );
  return (res.data.permissions ?? {}) as Record<string, PermissionLevel>;
}
