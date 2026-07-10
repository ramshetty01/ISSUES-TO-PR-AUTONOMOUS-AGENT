/** Load per-repo budget defaults from policies/budget-defaults.yaml. */
import { readFileSync } from "node:fs";
import { parse } from "yaml";
import type { BudgetDefaults } from "@itpr/budget-ledger";

interface BudgetDefaultsFile {
  tokenCap?: number;
  dollarCap?: number;
  overrides?: Record<string, { tokenCap?: number; dollarCap?: number }>;
}

/** Safe fallback caps if the policy file is missing/empty. */
export const FALLBACK_DEFAULTS: BudgetDefaults = {
  tokenCap: 200_000,
  dollarCap: 5,
};

export function loadBudgetDefaults(path: string): BudgetDefaults {
  const doc = parse(readFileSync(path, "utf8")) as BudgetDefaultsFile | null;
  if (!doc) return FALLBACK_DEFAULTS;
  return {
    tokenCap: doc.tokenCap ?? FALLBACK_DEFAULTS.tokenCap,
    dollarCap: doc.dollarCap ?? FALLBACK_DEFAULTS.dollarCap,
    ...(doc.overrides ? { overrides: doc.overrides } : {}),
  };
}
