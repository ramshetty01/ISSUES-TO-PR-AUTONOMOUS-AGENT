/**
 * Rolling daily budget window. Windows are UTC calendar days; spend resets when
 * the day rolls over.
 */

export interface DailyWindow {
  /** ISO-8601 start (inclusive), 00:00:00Z. */
  start: string;
  /** ISO-8601 end (exclusive), next day 00:00:00Z. */
  end: string;
  /** YYYY-MM-DD key for the window. */
  key: string;
}

/** Compute the UTC daily window containing `now`. */
export function dailyWindow(now: Date = new Date()): DailyWindow {
  const y = now.getUTCFullYear();
  const m = now.getUTCMonth();
  const d = now.getUTCDate();
  const start = new Date(Date.UTC(y, m, d, 0, 0, 0, 0));
  const end = new Date(Date.UTC(y, m, d + 1, 0, 0, 0, 0));
  const key = start.toISOString().slice(0, 10);
  return { start: start.toISOString(), end: end.toISOString(), key };
}

/** True when `at` (ISO-8601) falls inside the window. */
export function inWindow(window: DailyWindow, at: string): boolean {
  return at >= window.start && at < window.end;
}
