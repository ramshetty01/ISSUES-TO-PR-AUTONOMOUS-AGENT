/**
 * Repository allowlist — DENY BY DEFAULT. Only repos matching an allowlist
 * entry are processed. An entry name of "*" allows all repos under an owner.
 */
import type { RepoRef, AllowlistEntry } from "@itpr/shared-types";

export function isAllowedRepo(
  repo: RepoRef,
  allowlist: AllowlistEntry[],
): boolean {
  return allowlist.some(
    (e) =>
      e.owner === repo.owner && (e.name === "*" || e.name === repo.name),
  );
}
