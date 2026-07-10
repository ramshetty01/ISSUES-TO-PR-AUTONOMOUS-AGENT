# issue-to-pr-agent

An autonomous agent that turns a labeled GitHub issue into a reviewed pull request — running entirely on a **$0, self-hostable stack** (free-tier / local LLMs, LocalStack, self-hosted Langfuse). Safety and budgets are hard boundaries, not suggestions.

> **Flow:** issue labeled `agent-fix` → webhook → GitHub App (verify + filter + enqueue) → dispatcher (budget + repo-policy gates → sandboxed worker) → worker (understand → fix → verify → open PR) → traces in Langfuse, artifacts in S3, everything on the dashboard.

---

## How it works

```
GitHub issue (labeled)
      │  webhook (HMAC-verified, replay-protected)
      ▼
apps/github-app ──enqueue──▶ SQS (LocalStack)
      │                          │
      │                          ▼
      │                   apps/dispatcher ──budget + branch-protection + repo-policy gates──▶ docker run worker
      │                                                                                            │
      ▼                                                                                            ▼
  policies/*.yaml  ◀── single source of truth ──▶  worker/ pipeline:
                                                    context → agent loop → safety gate →
                                                    verification (tests/forbidden-paths/diff-size) →
                                                    PR authoring → observability + storage
```

- **Deny-by-default everywhere:** only allowlisted, branch-protected repos are processed; only issues carrying the trigger label; the worker refuses forbidden paths, secrets, force-pushes, and denied commands.
- **Budgets enforced even at $0:** free-tier providers meter tokens, so token *and* dollar caps apply per repo.
- **Same code, local → cloud:** the worker/dispatcher speak the AWS SDK against a swappable endpoint (LocalStack today, AWS later — see [docs/cloud-migration.md](docs/cloud-migration.md)).

---

## Repository layout

| Path | What |
|---|---|
| `worker/` | Python worker: bootstrap → agent loop → verification → safety → PR authoring → observability/storage (`pipeline.py` orchestrates it) |
| `apps/github-app/` | Express GitHub App: webhook verification, event filters, job enqueue |
| `apps/dispatcher/` | Poller: budget/policy gates, runs the sandboxed worker container |
| `apps/dashboard/` | Next.js operator UI: runs, budgets, cost, traces, safety events |
| `packages/` | Shared TS libs: `shared-types`, `config`, `github-client`, `budget-ledger`, `log-redaction` |
| `policies/` | Declarative rules (allowlist, labels, forbidden paths, denylist, budgets, provider limits) — read by every service |
| `infra/local/` | LocalStack + Langfuse + Postgres compose and init scripts |
| `eval/` | 30-issue eval harness with a zero-token mock path |
| `scripts/` | Setup + local-run helpers (GitHub App, smee, Ollama, worker image, …) |
| `security/` | Threat model, redaction test vectors, forbidden-diff examples |
| `docs/` | Architecture, safety/budget policy, migration, comparisons (index below) |

---

## Quickstart

**Prerequisites:** Docker (Compose v2), Node **≥ 22**, pnpm 9, Python 3.11, `gh`. (Ollama optional, for a local model.)

```bash
git clone https://github.com/ramshetty01/ISSUES-TO-PR-AUTONOMOUS-AGENT.git
cd ISSUES-TO-PR-AUTONOMOUS-AGENT

pnpm install && pnpm -r build          # TypeScript workspace
python3 -m venv .venv && source .venv/bin/activate
pip install -e "worker[dev]"           # Python worker
```

Prove it works with **zero keys** (mock provider, $0):

```bash
make eval                              # 100% pass, $0 — the agent→verify→metrics pipeline
cd worker && python -m pytest tests/test_pipeline.py -q   # end-to-end run pipeline
```

Then pick a track:

| Track | What you get | Command(s) |
|---|---|---|
| **A — Smoke** | pipeline proven, no keys | `make eval` (above) |
| **B — Local model** | a real coding model, no cloud | `./scripts/setup-ollama.sh` → `LLM_PROVIDER_ORDER=ollama,mock` |
| **C — Full E2E** | real webhook → **opened PR** | GitHub App + smee + `make up` / `make seed` (below) |

**Full end-to-end (Track C):**

```bash
cp .env.example .env                   # fill the GitHub App section
./scripts/setup-github-app.sh          # create the App (Issues/PRs/Contents: RW)
./scripts/setup-smee.sh                # webhook forwarding → writes SMEE_URL to .env
make up && make seed                   # LocalStack + Langfuse + apps; create queues/table/bucket
# add your repo to policies/repo-allowlist.yaml (deny-by-default!)
make worker-image                      # build itpr-worker:local
pnpm tsx scripts/create-test-issues.ts YOUR_ORG/YOUR_REPO agent-fix   # → triggers a run → PR
```

Observe: **Langfuse** at http://localhost:3000, **dashboard** at `pnpm --filter @itpr/dashboard dev -- -p 3002` (note: `:3000` is taken by Langfuse).

📖 **Full step-by-step guide, checklists, and troubleshooting:** [Issue #85](https://github.com/ramshetty01/ISSUES-TO-PR-AUTONOMOUS-AGENT/issues/85).

---

## Common commands

```bash
make up | down | seed | eval | worker-image | logs | ps   # local stack
pnpm -r build | test | typecheck                          # TypeScript workspace
cd worker && pytest -q && ruff check .                    # Python worker
```

---

## Tech & providers

- **Worker:** Python 3.11 (pydantic, boto3). **Services:** Node 20+/TypeScript (Express, Next.js), pnpm workspaces.
- **LLM providers (free-tier, fallback order):** NVIDIA NIM · Gemini · Groq · Ollama (local) · `mock` (always last). See [docs/llm-provider-strategy.md](docs/llm-provider-strategy.md).
- **Infra:** LocalStack (SQS/DynamoDB/S3) · self-hosted Langfuse + Postgres.

## Testing & CI

Every PR runs (zero external cost): TypeScript build + tests, Python worker tests + `ruff`, worker image build, and a **mock-provider smoke eval** (`.github/workflows/`). See [docs/ci-verification-gates.md](docs/ci-verification-gates.md).

## Safety & budgets

The hard boundary: forbidden-path refusals, secret/PII redaction, no force-push / protected-branch writes, command denylist, workspace jail, and per-repo token+dollar caps. See [docs/safety-policy.md](docs/safety-policy.md), [docs/budget-policy.md](docs/budget-policy.md), and [security/](security/).

---

## Documentation

- [Architecture](docs/architecture.md) · [Threat model](docs/threat-model.md) · [Sandbox design](docs/sandbox-design.md)
- [Safety policy](docs/safety-policy.md) · [Budget policy](docs/budget-policy.md) · [CI verification gates](docs/ci-verification-gates.md)
- [GitHub App permissions](docs/github-app-permissions.md) · [Branch-protection requirements](docs/branch-protection-requirements.md)
- [LLM provider strategy](docs/llm-provider-strategy.md) · [Dockerfile synthesis](docs/dockerfile-synthesis.md)
- [Cloud migration (LocalStack → AWS)](docs/cloud-migration.md) · [Eval methodology](docs/eval-methodology.md)
- Comparisons: [Cursor background agents](docs/comparison-cursor-background-agents.md) · [AWS remote SWE agents](docs/comparison-aws-remote-swe-agents.md)
- [Final write-up](docs/final-writeup.md) · [Eval harness](eval/README.md)

## License

[MIT](LICENSE).
