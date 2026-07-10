import type { LedgerEntry } from "@itpr/shared-types";

import { CostChart } from "../../components/CostChart.js";
import { RepoBudgetTable } from "../../components/RepoBudgetTable.js";
import { api } from "../../lib/api.js";

/** Cross-repo budget table + aggregate cost chart (spend per repo). */
export default async function BudgetsPage() {
  const budgets = await api.listBudgets();
  // Aggregate spend per repo into the provider-agnostic chart shape.
  const entries: LedgerEntry[] = budgets.map((b, i) => ({
    id: `agg-${i}`,
    repo: b.repo,
    runId: "",
    provider: `${b.repo.owner}/${b.repo.name}`,
    tokens: { input: 0, output: 0, total: b.tokensSpent },
    dollars: b.dollarsSpent,
    at: b.periodStart,
  }));
  return (
    <div className="grid">
      <h1>Budgets</h1>
      <section className="panel">
        <RepoBudgetTable budgets={budgets} />
      </section>
      <section className="panel grid">
        <h2>Spend by repo</h2>
        <CostChart entries={entries} />
      </section>
    </div>
  );
}
