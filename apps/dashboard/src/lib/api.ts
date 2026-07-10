/**
 * Typed data-access for the dashboard. Reads runs / budgets / repos from the
 * dispatcher+ledger API (or LocalStack in dev). All response shapes come from
 * @itpr/shared-types so the UI never invents its own contract.
 *
 * `fetchImpl` is injectable so tests exercise the client without a network.
 */
import type {
  BudgetWindow,
  LedgerEntry,
  RepoRef,
  RunSummary,
} from "@itpr/shared-types";

export interface ApiClientOptions {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
}

const DEFAULT_BASE =
  (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_BASE) ||
  "http://localhost:8080";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly path: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class ApiClient {
  private readonly baseUrl: string;
  private readonly fetchImpl: typeof fetch;

  constructor(opts: ApiClientOptions = {}) {
    this.baseUrl = (opts.baseUrl ?? DEFAULT_BASE).replace(/\/$/, "");
    this.fetchImpl = opts.fetchImpl ?? fetch;
  }

  private async get<T>(path: string): Promise<T> {
    const res = await this.fetchImpl(`${this.baseUrl}${path}`, {
      headers: { accept: "application/json" },
    });
    if (!res.ok) {
      throw new ApiError(`GET ${path} failed (${res.status})`, res.status, path);
    }
    return (await res.json()) as T;
  }

  listRuns(): Promise<RunSummary[]> {
    return this.get<RunSummary[]>("/api/runs");
  }

  getRun(runId: string): Promise<RunSummary> {
    return this.get<RunSummary>(`/api/runs/${encodeURIComponent(runId)}`);
  }

  listBudgets(): Promise<BudgetWindow[]> {
    return this.get<BudgetWindow[]>("/api/budgets");
  }

  getRepoBudget(owner: string, repo: string): Promise<BudgetWindow> {
    return this.get<BudgetWindow>(
      `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/budget`,
    );
  }

  listRepoLedger(owner: string, repo: string): Promise<LedgerEntry[]> {
    return this.get<LedgerEntry[]>(
      `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/ledger`,
    );
  }

  listRepos(): Promise<RepoRef[]> {
    return this.get<RepoRef[]>("/api/repos");
  }
}

/** Shared default client (localhost API base). */
export const api = new ApiClient();
