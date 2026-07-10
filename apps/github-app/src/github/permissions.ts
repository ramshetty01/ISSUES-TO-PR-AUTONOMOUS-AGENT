/**
 * Verify a GitHub App installation grants the scopes the agent needs. The
 * agent must be able to read issues, open PRs, and push branch contents.
 */

export type PermissionLevel = "read" | "write" | "admin";
export type InstallationPermissions = Record<string, PermissionLevel>;

/** Scopes the agent requires, each at least at "write". */
export const REQUIRED_SCOPES = [
  "issues",
  "pull_requests",
  "contents",
] as const;

export type RequiredScope = (typeof REQUIRED_SCOPES)[number];

export interface PermissionCheck {
  ok: boolean;
  missing: RequiredScope[];
}

const satisfiesWrite = (level: PermissionLevel | undefined): boolean =>
  level === "write" || level === "admin";

/** Check that all required scopes are present at write level or above. */
export function verifyPermissions(
  perms: InstallationPermissions,
): PermissionCheck {
  const missing = REQUIRED_SCOPES.filter((s) => !satisfiesWrite(perms[s]));
  return { ok: missing.length === 0, missing };
}

/** Human-readable refusal message for missing scopes. */
export function permissionRefusal(missing: RequiredScope[]): string {
  return (
    "This app installation is missing required permissions: " +
    missing.map((s) => `${s}:write`).join(", ") +
    ". Grant them in the installation settings and re-trigger."
  );
}
