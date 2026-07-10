# Final Write-up

`issue-to-pr-agent` is an end-to-end autonomous software engineer: label a GitHub
issue and it opens a reviewed pull request that fixes it — safely, cheaply, and
observably. This document summarizes what was built, the design choices behind
it, and how to run and evaluate it.

## What it does

A maintainer applies the `agent-fix` label to a well-scoped issue. The system
receives the webhook, enqueues a job, gates it on budget and branch protection,
runs an LLM-driven agent inside a sandboxed container, and — only after its own
verification passes — opens a PR for human review. CI independently re-verifies
the change. See the [architecture](architecture.md) for the full flow.

## Design principles

1. **Safety is code and policy, never prompt.** Guardrails
   ([safety policy](safety-policy.md)) live in
   [`policies/`](../policies) and the worker's `safety/` module. The LLM cannot
   argue its way past a hard reject.
2. **Fail closed at every layer.** No budget decision, no run. No branch
   protection, no run. Any forbidden edit or detected secret aborts the run.
3. **Zero-cost by default.** [Free-tier providers](llm-provider-strategy.md) with
   a `mock` floor, and a token [budget](budget-policy.md) that bounds spend even
   when dollars are $0.
4. **Local-first, cloud-ready.** LocalStack + Docker for development; a pure
   endpoint swap to AWS ([cloud migration](cloud-migration.md)).
5. **Observable.** Every run emits a trace; artifacts are scrubbed before storage
   or export ([`scrub-trace-archives.py`](../scripts/scrub-trace-archives.py)).

## What was built

- Four services: [`apps/github-app`](../apps/github-app),
  [`apps/dispatcher`](../apps/dispatcher), [`worker/`](../worker),
  [`apps/dashboard`](../apps/dashboard).
- Shared packages under [`packages/`](../packages): config, github-client,
  budget-ledger, log-redaction, shared-types.
- A policy-as-data layer, a security layer with a full
  [threat model](threat-model.md), and an eval harness
  ([eval methodology](eval-methodology.md)).
- Ops: setup/run [scripts](../scripts), CI workflows including a zero-token
  [mock eval gate](ci-verification-gates.md), issue/PR templates, and this docs
  set.

## Running it

```bash
pnpm install
scripts/setup-github-app.sh      # create the App, fill .env
scripts/setup-smee.sh            # webhook forwarding
scripts/build-worker-image.sh    # itpr-worker:local
pnpm dlx tsx scripts/run-local-webhook.ts     # start the App
pnpm dlx tsx scripts/run-local-dispatcher.ts  # start the dispatcher
pnpm dlx tsx scripts/create-test-issues.ts owner/repo  # seed test issues
```

## Evaluation

Quality is measured with an internal eval harness over seeded issues, with a
zero-token mock smoke subset in CI and model/provider ablations offline. See
[eval methodology](eval-methodology.md) and the comparisons with
[Cursor background agents](comparison-cursor-background-agents.md) and
[AWS remote SWE agents](comparison-aws-remote-swe-agents.md).

## Limitations & future work

Docker isolation should become microVMs for untrusted repos
([residual risks](../security/threat-model/residual-risks.md)); the agent targets
small, verifiable fixes rather than large refactors; and secret detection is
regex-based. These are documented rather than hidden — see the
[threat model](threat-model.md) and [safety policy](safety-policy.md).
