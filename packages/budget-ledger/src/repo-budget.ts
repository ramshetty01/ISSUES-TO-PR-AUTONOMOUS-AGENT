/** Per-repo budget cap resolution. */
import type { RepoRef } from "@itpr/shared-types";

export interface BudgetCaps {
  /** Daily token cap (0 = disabled/unlimited). */
  tokenCap: number;
  /** Daily dollar cap. */
  dollarCap: number;
}

/** Default caps applied when a repo has no explicit override. */
export interface BudgetDefaults extends BudgetCaps {
  /** Per-repo overrides keyed by "owner/name". */
  overrides?: Record<string, Partial<BudgetCaps>>;
}

const key = (repo: RepoRef) => `${repo.owner}/${repo.name}`;

/** Resolve the effective caps for a repo, merging defaults with any override. */
export function resolveCaps(repo: RepoRef, defaults: BudgetDefaults): BudgetCaps {
  const override = defaults.overrides?.[key(repo)];
  return {
    tokenCap: override?.tokenCap ?? defaults.tokenCap,
    dollarCap: override?.dollarCap ?? defaults.dollarCap,
  };
}
