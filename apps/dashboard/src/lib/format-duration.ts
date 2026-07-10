/** Presentation helpers for elapsed time, used by the run timeline + cards. */

/** Human-readable duration from milliseconds (e.g. `820ms`, `1.2s`, `3m 4s`, `1h 2m`). */
export function formatDuration(ms: number): string {
  if (!Number.isFinite(ms) || ms < 0) return "—";
  if (ms < 1_000) return `${Math.round(ms)}ms`;
  const totalSeconds = Math.floor(ms / 1_000);
  if (totalSeconds < 60) {
    const s = ms / 1_000;
    return `${s.toFixed(s < 10 ? 1 : 0)}s`;
  }
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes < 60) return `${minutes}m ${seconds}s`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m`;
}

/** Duration between two ISO-8601 timestamps; `—` if either is missing/invalid. */
export function durationBetween(startIso: string, endIso?: string): string {
  const start = Date.parse(startIso);
  const end = endIso ? Date.parse(endIso) : Date.now();
  if (Number.isNaN(start) || Number.isNaN(end)) return "—";
  return formatDuration(end - start);
}
