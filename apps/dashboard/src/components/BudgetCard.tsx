import type { BudgetWindow } from "@itpr/shared-types";

import { formatCost, formatTokens, percentOfCap } from "../lib/format-cost.js";

export interface BudgetCardProps {
  budget: BudgetWindow;
}

/** A single repo's budget window: token + dollar spend against caps. */
export function BudgetCard({ budget }: BudgetCardProps) {
  const tokenPct = percentOfCap(budget.tokensSpent, budget.tokenCap);
  const dollarPct = percentOfCap(budget.dollarsSpent, budget.dollarCap);
  return (
    <article className="panel grid" aria-label="budget card">
      <header>
        <strong>
          {budget.repo.owner}/{budget.repo.name}
        </strong>
      </header>
      <div>
        <div className="muted">Tokens</div>
        <div>
          {formatTokens(budget.tokensSpent)} / {formatTokens(budget.tokenCap)}{" "}
          <span className="muted">({tokenPct}%)</span>
        </div>
        <Meter percent={tokenPct} />
      </div>
      <div>
        <div className="muted">Cost</div>
        <div>
          {formatCost(budget.dollarsSpent)} / {formatCost(budget.dollarCap)}{" "}
          <span className="muted">({dollarPct}%)</span>
        </div>
        <Meter percent={dollarPct} />
      </div>
    </article>
  );
}

function Meter({ percent }: { percent: number }) {
  const color = percent >= 90 ? "var(--danger)" : percent >= 70 ? "var(--warn)" : "var(--ok)";
  return (
    <div
      role="meter"
      aria-valuenow={percent}
      aria-valuemin={0}
      aria-valuemax={100}
      style={{ background: "var(--border)", borderRadius: 999, height: 6 }}
    >
      <div style={{ width: `${percent}%`, background: color, height: 6, borderRadius: 999 }} />
    </div>
  );
}

export default BudgetCard;
