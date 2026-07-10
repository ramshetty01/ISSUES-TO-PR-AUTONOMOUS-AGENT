import type { LedgerEntry } from "@itpr/shared-types";

import { formatCost } from "../lib/format-cost.js";

export interface CostChartProps {
  entries: LedgerEntry[];
}

/** Dependency-free SVG bar chart of imputed cost by provider. */
export function CostChart({ entries }: CostChartProps) {
  const byProvider = new Map<string, number>();
  for (const e of entries) {
    byProvider.set(e.provider, (byProvider.get(e.provider) ?? 0) + e.dollars);
  }
  const bars = [...byProvider.entries()].map(([provider, dollars]) => ({ provider, dollars }));
  if (bars.length === 0) {
    return <p className="muted">No spend recorded.</p>;
  }
  const max = Math.max(...bars.map((b) => b.dollars), 0.0001);
  const barHeight = 22;
  const gap = 8;
  const width = 320;
  const labelW = 90;

  return (
    <svg
      role="img"
      aria-label="cost by provider"
      width="100%"
      viewBox={`0 0 ${width} ${bars.length * (barHeight + gap)}`}
    >
      {bars.map((b, i) => {
        const y = i * (barHeight + gap);
        const w = Math.round(((width - labelW - 60) * b.dollars) / max);
        return (
          <g key={b.provider} transform={`translate(0 ${y})`}>
            <text x={0} y={barHeight * 0.7} fill="var(--muted)" fontSize={12}>
              {b.provider}
            </text>
            <rect
              x={labelW}
              y={2}
              width={Math.max(w, b.dollars > 0 ? 2 : 0)}
              height={barHeight - 4}
              rx={3}
              fill="var(--accent)"
            />
            <text x={labelW + w + 6} y={barHeight * 0.7} fill="var(--text)" fontSize={12}>
              {formatCost(b.dollars)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default CostChart;
