/**
 * Presentation helpers for money + token counts. Free-tier providers meter
 * tokens at $0, so a run can be meaningful work yet cost nothing — hence the
 * explicit "Free" rendering.
 */

/** Format imputed dollars for display (e.g. `$1.23`, or `Free` at $0). */
export function formatCost(dollars: number): string {
  if (!Number.isFinite(dollars)) return "—";
  if (dollars <= 0) return "Free";
  if (dollars < 0.01) return "<$0.01";
  return `$${dollars.toFixed(2)}`;
}

/** Compact token count (e.g. `950`, `1.2k`, `3.4M`). */
export function formatTokens(total: number): string {
  if (!Number.isFinite(total) || total < 0) return "—";
  if (total < 1_000) return String(Math.round(total));
  if (total < 1_000_000) return `${(total / 1_000).toFixed(1)}k`;
  return `${(total / 1_000_000).toFixed(1)}M`;
}

/** Fraction of a cap consumed, clamped to 0–100 (%). */
export function percentOfCap(spent: number, cap: number): number {
  if (!Number.isFinite(spent) || !Number.isFinite(cap) || cap <= 0) return 0;
  return Math.min(100, Math.max(0, Math.round((spent / cap) * 100)));
}
