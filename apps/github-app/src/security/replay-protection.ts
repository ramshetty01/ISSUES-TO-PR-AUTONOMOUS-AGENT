/**
 * Reject replayed webhook deliveries. GitHub delivery ids (X-GitHub-Delivery)
 * are unique per delivery; we remember recently-seen ids for a TTL window and
 * reject duplicates. In-memory is sufficient for the single-node local build;
 * a shared store slots in behind the same interface later.
 */

export interface ReplayGuardOptions {
  /** How long a delivery id is remembered, in ms. Default 10 minutes. */
  ttlMs?: number;
  /** Clock injection for tests. */
  now?: () => number;
}

export class ReplayGuard {
  private readonly seen = new Map<string, number>();
  private readonly ttlMs: number;
  private readonly now: () => number;

  constructor(opts: ReplayGuardOptions = {}) {
    this.ttlMs = opts.ttlMs ?? 10 * 60 * 1000;
    this.now = opts.now ?? Date.now;
  }

  /**
   * Record a delivery id. Returns true if it is fresh (accept), false if it was
   * already seen within the TTL window (replay — reject).
   */
  check(deliveryId: string): boolean {
    const t = this.now();
    this.evict(t);
    if (this.seen.has(deliveryId)) return false;
    this.seen.set(deliveryId, t);
    return true;
  }

  private evict(t: number): void {
    for (const [id, seenAt] of this.seen) {
      if (t - seenAt > this.ttlMs) this.seen.delete(id);
    }
  }

  /** Number of ids currently remembered (for tests/metrics). */
  get size(): number {
    return this.seen.size;
  }
}
