# Budget Policy

Every run costs tokens even when the dollar cost is zero, because the agent
relies on [free-tier providers](llm-provider-strategy.md) that meter tokens and
requests. The budget layer prevents a single repo — or a runaway loop — from
exhausting a provider's daily quota or an operator's paid budget.

## Model

Budgets are per-repo and windowed (daily by default). The
[`@itpr/budget-ledger`](../packages/budget-ledger) package implements an
append-only ledger over DynamoDB in production and SQLite locally
(`BUDGET_LEDGER_FALLBACK_SQLITE=true`). Both backends share the same arithmetic
(`ledger.ts`) so verdicts are identical.

Two caps apply per window
([`policies/budget-defaults.yaml`](../policies/budget-defaults.yaml)):

- `tokenCap` — total tokens across all providers (default `200000`).
- `dollarCap` — dollars imputed at provider list price (default `5`), so paid
  fallbacks are bounded even when free tiers are exhausted.

Per-repo overrides are keyed by `owner/name`; see
[`examples/budget.example.yaml`](../examples/budget.example.yaml).

## Enforcement

The dispatcher's budget gate calls `checkAndReserve` **before** starting the
worker. It atomically sums the current window and, if the estimate fits, reserves
it; otherwise it returns a `BudgetVerdict` with `allowed: false` and the job is
rejected (commented back on the issue, not silently dropped). Reservation is
idempotent via the estimate `id`, so a redelivered SQS message can't
double-spend. After the run, actual usage is recorded with `recordSpend`.

If the ledger backend is unreachable, `LedgerUnavailable` is raised and the
dispatcher fails closed — no run proceeds without a budget decision.

## Interaction with provider limits

The token cap is deliberately independent of, and usually tighter than, the raw
provider [rate limits](../policies/llm-provider-limits.yaml). Rate limits protect
the provider (requests/minute); the budget protects the operator (tokens/day per
repo). The worker's rate limiter (`llm/rate_limiter.py`) handles the former; the
ledger handles the latter.

## Seeding & inspection

Use [`seed-budget-ledger.ts`](../scripts/seed-budget-ledger.ts) to populate the
local SQLite ledger for dashboard/dev testing. The dashboard reads the same
ledger to render per-repo spend against caps.

## Related

- [LLM provider strategy](llm-provider-strategy.md) — the providers and their
  free-tier caps.
- [Safety policy](safety-policy.md) — the guardrail that runs alongside budget.
- [Architecture](architecture.md) — where the gate sits in the flow.
