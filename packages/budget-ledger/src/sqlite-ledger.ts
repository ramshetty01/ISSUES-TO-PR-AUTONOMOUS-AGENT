/**
 * Zero-dependency sqlite ledger backend (node:sqlite). Used as the fallback
 * when LocalStack/DynamoDB is unavailable, and as the always-on backend in
 * tests. Reservation is done inside a transaction so concurrent checks cannot
 * double-count.
 */
import { createRequire } from "node:module";
import type { DatabaseSync as DatabaseSyncType } from "node:sqlite";
import type { RepoRef, LedgerEntry } from "@itpr/shared-types";

// node:sqlite is a recent builtin that some bundlers (vite/vitest) fail to
// resolve statically; load it at runtime so only the running Node evaluates it.
const nodeRequire = createRequire(import.meta.url);
const { DatabaseSync } = nodeRequire("node:sqlite") as {
  DatabaseSync: new (path?: string) => DatabaseSyncType;
};
import { BaseLedger, fits, type Ledger, type LedgerStore } from "./ledger.js";
import type { BudgetCaps } from "./repo-budget.js";

class SqliteStore implements LedgerStore {
  private readonly db: DatabaseSyncType;

  constructor(path = ":memory:") {
    this.db = new DatabaseSync(path);
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS ledger (
        id TEXT PRIMARY KEY,
        owner TEXT NOT NULL,
        name TEXT NOT NULL,
        run_id TEXT NOT NULL,
        provider TEXT NOT NULL,
        tokens INTEGER NOT NULL,
        dollars REAL NOT NULL,
        at TEXT NOT NULL
      );
      CREATE INDEX IF NOT EXISTS idx_ledger_repo_at ON ledger(owner, name, at);
    `);
  }

  async append(entry: LedgerEntry): Promise<void> {
    this.insert(entry);
  }

  private insert(entry: LedgerEntry): void {
    this.db
      .prepare(
        `INSERT OR IGNORE INTO ledger
           (id, owner, name, run_id, provider, tokens, dollars, at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      )
      .run(
        entry.id,
        entry.repo.owner,
        entry.repo.name,
        entry.runId,
        entry.provider,
        entry.tokens.total,
        entry.dollars,
        entry.at,
      );
  }

  async sum(
    repo: RepoRef,
    start: string,
    end: string,
  ): Promise<{ tokens: number; dollars: number }> {
    return this.sumSync(repo, start, end);
  }

  private sumSync(
    repo: RepoRef,
    start: string,
    end: string,
  ): { tokens: number; dollars: number } {
    const row = this.db
      .prepare(
        `SELECT COALESCE(SUM(tokens), 0) AS tokens,
                COALESCE(SUM(dollars), 0) AS dollars
           FROM ledger
          WHERE owner = ? AND name = ? AND at >= ? AND at < ?`,
      )
      .get(repo.owner, repo.name, start, end) as {
      tokens: number;
      dollars: number;
    };
    return { tokens: Number(row.tokens), dollars: Number(row.dollars) };
  }

  async reserve(
    repo: RepoRef,
    start: string,
    end: string,
    caps: BudgetCaps,
    entry: LedgerEntry,
  ): Promise<{ ok: boolean; tokens: number; dollars: number }> {
    this.db.exec("BEGIN IMMEDIATE");
    try {
      const spent = this.sumSync(repo, start, end);
      const ok = fits(caps, spent, {
        tokens: entry.tokens.total,
        dollars: entry.dollars,
      });
      if (ok) this.insert(entry);
      this.db.exec("COMMIT");
      return { ok, tokens: spent.tokens, dollars: spent.dollars };
    } catch (e) {
      this.db.exec("ROLLBACK");
      throw e;
    }
  }

  async close(): Promise<void> {
    this.db.close();
  }
}

/** Create a sqlite-backed ledger. Defaults to an in-memory database. */
export function createSqliteLedger(path = ":memory:"): Ledger {
  return new BaseLedger(new SqliteStore(path));
}
