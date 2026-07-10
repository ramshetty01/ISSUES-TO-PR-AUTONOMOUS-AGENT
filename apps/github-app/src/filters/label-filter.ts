/**
 * Only events carrying an approved trigger label are processed. The allowed set
 * is sourced from policies/allowed-labels.yaml.
 */
import { readFileSync } from "node:fs";
import { parse } from "yaml";

/** True if any of the issue's labels is in the allowed trigger set. */
export function matchesTriggerLabel(
  labels: string[],
  allowed: string[],
): boolean {
  const set = new Set(allowed);
  return labels.some((l) => set.has(l));
}

/** The specific label that triggered, if any (first match wins). */
export function triggerLabel(
  labels: string[],
  allowed: string[],
): string | undefined {
  const set = new Set(allowed);
  return labels.find((l) => set.has(l));
}

interface AllowedLabelsFile {
  labels?: string[];
}

/** Load the allowed trigger labels from a YAML policy file. */
export function loadAllowedLabels(path: string): string[] {
  const doc = parse(readFileSync(path, "utf8")) as AllowedLabelsFile | null;
  return doc?.labels ?? [];
}
