/** In-memory dispatcher counters (a real exporter slots in behind this later). */

export type MetricName =
  | "received"
  | "dispatched"
  | "succeeded"
  | "refused"
  | "failed"
  | "dead_lettered"
  | "malformed";

export class Metrics {
  private readonly counts = new Map<MetricName, number>();

  inc(name: MetricName, by = 1): void {
    this.counts.set(name, (this.counts.get(name) ?? 0) + by);
  }

  get(name: MetricName): number {
    return this.counts.get(name) ?? 0;
  }

  snapshot(): Record<MetricName, number> {
    const out = {} as Record<MetricName, number>;
    for (const k of [
      "received",
      "dispatched",
      "succeeded",
      "refused",
      "failed",
      "dead_lettered",
      "malformed",
    ] as MetricName[]) {
      out[k] = this.get(k);
    }
    return out;
  }
}
