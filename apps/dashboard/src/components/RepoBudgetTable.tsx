import type { BudgetWindow } from "@itpr/shared-types";

import { formatCost, formatTokens, percentOfCap } from "../lib/format-cost.js";

export interface RepoBudgetTableProps {
  budgets: BudgetWindow[];
}

/** Tabular budget overview across all repos, linking to each repo page. */
export function RepoBudgetTable({ budgets }: RepoBudgetTableProps) {
  if (budgets.length === 0) {
    return <p className="muted">No repos with budgets yet.</p>;
  }
  return (
    <table aria-label="repo budgets">
      <thead>
        <tr>
          <th>Repo</th>
          <th>Tokens</th>
          <th>Cost</th>
          <th>Used</th>
        </tr>
      </thead>
      <tbody>
        {budgets.map((b) => {
          const pct = Math.max(
            percentOfCap(b.tokensSpent, b.tokenCap),
            percentOfCap(b.dollarsSpent, b.dollarCap),
          );
          const slug = `${b.repo.owner}/${b.repo.name}`;
          return (
            <tr key={slug}>
              <td>
                <a href={`/repos/${b.repo.owner}/${b.repo.name}`}>{slug}</a>
              </td>
              <td>
                {formatTokens(b.tokensSpent)} / {formatTokens(b.tokenCap)}
              </td>
              <td>
                {formatCost(b.dollarsSpent)} / {formatCost(b.dollarCap)}
              </td>
              <td>{pct}%</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

export default RepoBudgetTable;
