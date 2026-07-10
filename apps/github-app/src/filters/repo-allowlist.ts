/**
 * Repository allowlist — DENY BY DEFAULT. Only repos matching an allowlist
 * entry are processed. An entry name of "*" allows all repos under an owner.
 */
import { existsSync, readFileSync } from "node:fs";
import { parse } from "yaml";
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

interface AllowlistFile {
  allowlist?: AllowlistEntry[];
}

/**
 * Load the allowlist from a YAML policy file. Missing/empty file yields an empty
 * list (deny-all) — the safe default.
 */
export function loadAllowlist(path: string): AllowlistEntry[] {
  if (!existsSync(path)) return [];
  const doc = parse(readFileSync(path, "utf8")) as AllowlistFile | null;
  return doc?.allowlist ?? [];
}
