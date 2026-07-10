/**
 * seed-budget-ledger.ts — write a few spend entries into the budget ledger so
 * the dashboard and the dispatcher's budget gate have data to show / enforce
 * against in local dev. Uses the sqlite fallback ledger by default (no AWS
 * needed); see packages/budget-ledger and docs/budget-policy.md.
 *
 *   pnpm dlx tsx scripts/seed-budget-ledger.ts owner/repo [sqlite-path]
 *
 * With no sqlite-path it uses ./.itpr-budget.sqlite in the repo root.
 */
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import {
  createSqliteLedger,
  resolveCaps,
  type BudgetDefaults,
} from "@itpr/budget-ledger";
import type { LedgerEntry, RepoRef } from "@itpr/shared-types";

const here = dirname(fileURLToPath(import.meta.url));

const DEFAULTS: BudgetDefaults = { tokenCap: 200_000, dollarCap: 5 };

function entry(repo: RepoRef, i: number): LedgerEntry {
  const input = 800 + i * 250;
  const output = 400 + i * 120;
  return {
    id: `seed-${repo.owner}-${repo.name}-${i}`,
    repo,
    runId: `seed-run-${i}`,
    provider: ["groq", "gemini", "nvidia_nim", "mock"][i % 4],
    tokens: { input, output, total: input + output },
    // Free-tier providers cost $0 in dollars but still meter tokens.
    dollars: Number(((input + output) * 0.0000006).toFixed(6)),
    at: new Date(Date.now() - i * 3_600_000).toISOString(),
  };
}

async function main(): Promise<void> {
  const target = process.argv[2];
  if (!target || !target.includes("/")) {
    console.error("usage: tsx scripts/seed-budget-ledger.ts owner/repo [sqlite-path]");
    process.exit(2);
  }
  const [owner, name] = target.split("/");
  const repo: RepoRef = { owner, name };
  const dbPath = process.argv[3] ?? resolve(here, "../.itpr-budget.sqlite");

  const ledger = createSqliteLedger(dbPath);
  try {
    for (let i = 0; i < 5; i++) {
      await ledger.recordSpend(entry(repo, i));
    }
    const caps = resolveCaps(repo, DEFAULTS);
    const window = await ledger.getWindow(repo, caps);
    console.log(`seeded 5 entries into ${dbPath}`);
    console.log(
      `today: ${window.tokensSpent}/${window.tokenCap} tokens, ` +
        `$${window.dollarsSpent.toFixed(4)}/$${window.dollarCap}`,
    );
  } finally {
    await ledger.close();
  }
}

main().catch((err) => {
  console.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
