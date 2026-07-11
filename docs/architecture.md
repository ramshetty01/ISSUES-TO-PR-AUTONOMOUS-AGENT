# Architecture

`issue-to-pr-agent` turns a labeled GitHub issue into a reviewed pull request
without a human in the loop for the mechanical work. It is a pnpm + Python
monorepo split into four runtime services plus shared packages and policy.

## Components

| Component | Path | Runtime | Responsibility |
| --- | --- | --- | --- |
| GitHub App | [`apps/github-app`](../apps/github-app) | Node >=22 | Receive + verify webhooks, filter by label/actor/repo, enqueue a normalized job |
| Dispatcher | [`apps/dispatcher`](../apps/dispatcher) | Node >=22 | Poll the queue, apply budget + branch-protection gates, run the worker container, ack/nack/DLQ |
| Worker | [`worker/`](../worker) | Python 3.11 in Docker | The agent loop: clone, plan, edit, run tests, open the PR — inside a sandbox |
| Dashboard | [`apps/dashboard`](../apps/dashboard) | Node >=22 | Read-only view of runs, budgets, and traces |

Shared TypeScript packages live under [`packages/`](../packages):
`shared-types`, `config`, `github-client`, `budget-ledger`, `log-redaction`.
Operating rules live under [`policies/`](../policies) and are loaded at runtime,
never hard-coded.

## Request flow

```
issue labeled ─► GitHub App ─► SQS queue ─► Dispatcher ─► Worker (Docker)
   (webhook)      verify+filter   job         gates         agent loop
                                                              │
                                              PR ◄────────────┘
```

1. A maintainer applies the `agent-fix` label. GitHub delivers a webhook
   (forwarded via smee.io in local dev — see
   [`setup-smee.sh`](../scripts/setup-smee.sh)).
2. The App verifies the HMAC signature, checks replay protection, sanitizes the
   payload, and enqueues a job onto SQS.
3. The Dispatcher polls SQS. Before running anything it checks the per-repo
   [budget](budget-policy.md) and [branch protection](branch-protection-requirements.md).
4. The Worker runs in a locked-down container ([sandbox design](sandbox-design.md)),
   drives the LLM ([provider strategy](llm-provider-strategy.md)) through an
   agentic loop, and enforces the [safety policy](safety-policy.md) on every
   tool call. It opens a PR only after its own verification gates pass.
5. CI re-verifies the PR ([verification gates](ci-verification-gates.md)).

## Infrastructure

Local dev runs on LocalStack (SQS + DynamoDB + S3) and self-hosted Langfuse for
traces. Production swaps endpoints for real AWS with no code change — see
[cloud migration](cloud-migration.md). The GitHub App needs a specific,
minimal permission set: [github-app-permissions.md](github-app-permissions.md).

## Local setup paths

The stack is designed to be brought up in three layers, so a fresh clone can
prove the core agent before any secrets are available.

### Track A: smoke run with no keys

Install the TypeScript and Python workspaces, then run:

```bash
pnpm install
pnpm -r build
python3 -m venv .venv
source .venv/bin/activate
pip install -e "worker[dev]"

make eval
cd worker && python -m pytest tests/test_pipeline.py -q
```

`make eval` uses the `mock` provider and the smoke subset. The worker pipeline
test exercises context handling, agent execution, safety gates, verification,
PR body generation, run summaries, and redacted artifact storage without
GitHub, Docker infrastructure, or LLM provider keys.

### Track B: local coding model

For a real model with no cloud spend, use Ollama:

```bash
./scripts/setup-ollama.sh
```

Then set:

```dotenv
LLM_PROVIDER_ORDER=ollama,mock
OLLAMA_HOST=http://localhost:11434
```

The default local endpoint is declared in
[`packages/config/src/defaults.ts`](../packages/config/src/defaults.ts), and
`mock` should stay last as the fallback provider.

### Track C: full webhook-to-PR run

Copy `.env.example`, create a GitHub App, and run the local stack:

```bash
cp .env.example .env
./scripts/setup-github-app.sh
./scripts/setup-smee.sh
make up
make seed
make worker-image
```

The agent is deny-by-default. Add the target repository to
[`policies/repo-allowlist.yaml`](../policies/repo-allowlist.yaml), keep the
trigger label from
[`policies/allowed-labels.yaml`](../policies/allowed-labels.yaml), and verify
branch protection:

```bash
pnpm tsx scripts/verify-branch-protection.ts YOUR_ORG/YOUR_REPO
```

Create a labeled test issue:

```bash
pnpm tsx scripts/create-test-issues.ts YOUR_ORG/YOUR_REPO agent-fix
```

The expected result is an opened PR after the dispatcher passes budget, policy,
and branch-protection gates and the worker passes its verification checks.

For a worker-only local run that skips webhook delivery and the dispatcher,
provide one normalized job payload:

```bash
./scripts/run-local-worker.sh path/to/job.json
```

## Observability and dashboard

Local Langfuse runs on `http://localhost:3000`. The dashboard is a Next.js app,
so run it on a different port during local development:

```bash
pnpm --filter @itpr/dashboard dev -- -p 3002
```

After adding `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` to `.env`, rerun a
job. The PR body should link to the trace, and the dashboard should show the run
timeline, trace link, safety events, and budget state.

## Security posture

The system is designed around a hostile-input assumption: issue text is
attacker-controlled. See the [threat model](threat-model.md) and the detailed
[`security/`](../security/threat-model) breakdown of attackers, assets, attack
paths, mitigations, and residual risks.

## Further reading

- [Safety policy](safety-policy.md) · [Budget policy](budget-policy.md)
- [CI verification gates](ci-verification-gates.md)
- [LLM provider strategy](llm-provider-strategy.md)
- [Final write-up](final-writeup.md)
