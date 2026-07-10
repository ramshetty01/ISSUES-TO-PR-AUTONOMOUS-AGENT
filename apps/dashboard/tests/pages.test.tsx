import type { BudgetWindow, LedgerEntry, RunSummary } from "@itpr/shared-types";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Mock the data-access layer; pages consume the shared `api` singleton.
// `vi.hoisted` runs before the hoisted vi.mock factory, so these are safe to reference.
const { listRuns, getRun, listBudgets, getRepoBudget, listRepoLedger, getRateLimit } =
  vi.hoisted(() => ({
    listRuns: vi.fn(),
    getRun: vi.fn(),
    listBudgets: vi.fn(),
    getRepoBudget: vi.fn(),
    listRepoLedger: vi.fn(),
    getRateLimit: vi.fn(),
  }));
vi.mock("../src/lib/api.js", () => ({
  api: { listRuns, getRun, listBudgets, getRepoBudget, listRepoLedger, getRateLimit },
}));

import BudgetsPage from "../src/app/budgets/page.js";
import HomePage from "../src/app/page.js";
import RepoPage from "../src/app/repos/[owner]/[repo]/page.js";
import RunPage from "../src/app/runs/[runId]/page.js";

const budget: BudgetWindow = {
  repo: { owner: "acme", name: "widgets" },
  periodStart: "2026-01-01T00:00:00Z",
  periodEnd: "2026-01-02T00:00:00Z",
  tokenCap: 100_000,
  dollarCap: 5,
  tokensSpent: 40_000,
  dollarsSpent: 2,
};

const run: RunSummary = {
  runId: "run-1",
  job: {
    id: "run-1",
    repo: { owner: "acme", name: "widgets" },
    installationId: 1,
    trigger: "issue_labeled",
    headSha: "abc",
    labels: [],
    createdAt: "2026-01-01T00:00:00Z",
    issueNumber: 7,
  },
  state: "succeeded",
  timeline: [{ at: "2026-01-01T00:00:00Z", kind: "plan", message: "Planned the fix" }],
  usage: { input: 100, output: 50, total: 150 },
  dollars: 0,
  safetyEvents: [],
  traceUrl: "http://localhost:3000/trace/run-1",
  startedAt: "2026-01-01T00:00:00Z",
  finishedAt: "2026-01-01T00:03:00Z",
};

const ledger: LedgerEntry[] = [
  {
    id: "e1",
    repo: { owner: "acme", name: "widgets" },
    runId: "run-1",
    provider: "groq",
    tokens: { input: 100, output: 50, total: 150 },
    dollars: 0,
    at: "2026-01-01T00:00:00Z",
  },
];

beforeEach(() => vi.clearAllMocks());

describe("HomePage", () => {
  it("lists recent runs linking to detail", async () => {
    listRuns.mockResolvedValue([run]);
    getRateLimit.mockResolvedValue({ throttled: false });
    render(await HomePage());
    expect(screen.getByRole("link", { name: "run-1" })).toHaveAttribute("href", "/runs/run-1");
  });

  it("surfaces a rate-limit banner when a provider is throttled", async () => {
    listRuns.mockResolvedValue([]);
    getRateLimit.mockResolvedValue({ throttled: true, provider: "groq" });
    render(await HomePage());
    expect(screen.getByRole("alert")).toHaveTextContent(/groq.*rate limit/i);
  });
});

describe("RunPage composes timeline + trace + safety", () => {
  it("renders the timeline and a resolving trace link", async () => {
    getRun.mockResolvedValue(run);
    render(await RunPage({ params: { runId: "run-1" } }));
    expect(screen.getByText("Planned the fix")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /langfuse trace/i })).toHaveAttribute(
      "href",
      "http://localhost:3000/trace/run-1",
    );
    expect(screen.getByText(/clean run/i)).toBeInTheDocument();
  });
});

describe("RepoPage", () => {
  it("renders budget card + cost chart", async () => {
    getRepoBudget.mockResolvedValue(budget);
    listRepoLedger.mockResolvedValue(ledger);
    render(await RepoPage({ params: { owner: "acme", repo: "widgets" } }));
    expect(screen.getByLabelText("budget card")).toBeInTheDocument();
    expect(screen.getByText("groq")).toBeInTheDocument();
  });
});

describe("BudgetsPage aggregates", () => {
  it("renders the repo budget table and per-repo spend chart", async () => {
    listBudgets.mockResolvedValue([budget]);
    render(await BudgetsPage());
    expect(screen.getByRole("link", { name: "acme/widgets" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /cost by provider/i })).toBeInTheDocument();
  });
});
