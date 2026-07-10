/**
 * Append-only audit log of every dispatch decision. Kept in memory here + echoed
 * to the logger; a durable sink (S3/DynamoDB) slots in behind record() later.
 */
import { logger } from "../logging/logger.js";

export type Decision =
  | "dispatched"
  | "succeeded"
  | "refused"
  | "failed"
  | "dead_lettered"
  | "malformed";

export interface AuditEntry {
  at: string;
  jobId: string;
  decision: Decision;
  reason?: string;
}

export class AuditLog {
  private readonly entries: AuditEntry[] = [];

  record(jobId: string, decision: Decision, reason?: string): void {
    const entry: AuditEntry = {
      at: new Date().toISOString(),
      jobId,
      decision,
      ...(reason ? { reason } : {}),
    };
    this.entries.push(entry);
    logger.info("audit", entry as unknown as Record<string, unknown>);
  }

  all(): readonly AuditEntry[] {
    return this.entries;
  }
}
