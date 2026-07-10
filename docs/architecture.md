# Architecture

`issue-to-pr-agent` turns a labeled GitHub issue into a reviewed pull request
without a human in the loop for the mechanical work. It is a pnpm + Python
monorepo split into four runtime services plus shared packages and policy.

## Components

| Component | Path | Runtime | Responsibility |
| --- | --- | --- | --- |
| GitHub App | [`apps/github-app`](../apps/github-app) | Node 20 | Receive + verify webhooks, filter by label/actor/repo, enqueue a normalized job |
| Dispatcher | [`apps/dispatcher`](../apps/dispatcher) | Node 20 | Poll the queue, apply budget + branch-protection gates, run the worker container, ack/nack/DLQ |
| Worker | [`worker/`](../worker) | Python 3.11 in Docker | The agent loop: clone, plan, edit, run tests, open the PR — inside a sandbox |
| Dashboard | [`apps/dashboard`](../apps/dashboard) | Node 20 | Read-only view of runs, budgets, and traces |

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
