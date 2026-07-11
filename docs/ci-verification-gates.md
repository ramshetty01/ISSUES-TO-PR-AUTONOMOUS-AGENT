# CI Verification Gates

There are two verification layers. The **worker** verifies its own change before
opening a PR (see [safety policy](safety-policy.md)). **CI** independently
re-verifies every PR — agent-authored or human — so a regression in the agent
cannot merge unchecked. This document covers the CI layer in
[`.github/workflows/`](../.github/workflows).

## Workflows

| Workflow | Trigger | What it enforces |
| --- | --- | --- |
| [`ci.yml`](../.github/workflows/ci.yml) | PR, push to `main` | Umbrella: fans out to the four below, then gates a single `ci-passed` status |
| [`test-typescript.yml`](../.github/workflows/test-typescript.yml) | PR/push touching TS | `pnpm install --frozen-lockfile`, `pnpm -r build`, `pnpm -r typecheck`, `pnpm -r test` |
| [`test-python-worker.yml`](../.github/workflows/test-python-worker.yml) | PR/push touching `worker/**` | `pip install .[dev]`, `ruff check`, `mypy` (soft), `pytest` |
| [`build-worker-image.yml`](../.github/workflows/build-worker-image.yml) | PR/push touching `worker/**` | `docker build` + an import smoke-test of the image |
| [`eval-internal.yml`](../.github/workflows/eval-internal.yml) | every PR | Mock-provider **zero-token** smoke eval over the `smoke` subset |
| [`release.yml`](../.github/workflows/release.yml) | tag `v*.*.*` | Re-verify, build + push image to GHCR, draft release |

Runtimes are pinned: Node 24 in CI, pnpm 9, Python 3.11. Local and container
development require Node >=22, matching the root `engines` field.

## The zero-token eval gate

`eval-internal.yml` runs
`python3 eval/runners/run_internal_eval.py --provider mock --subset smoke`. The
mock provider returns canned completions, so the job costs **no tokens and needs
no API keys**, yet it exercises the full eval path (load fixtures → plan → apply
→ score). This catches breakage in the eval harness and the agent's plumbing on
every PR without incurring cost or flakiness from live providers. See
[`docs/eval-methodology.md`](eval-methodology.md).

## Branch protection

The single required status check should be **`ci-passed`**, the aggregation job
in `ci.yml` that fails unless all fan-out jobs succeed. Combined with the
[branch-protection requirements](branch-protection-requirements.md) the agent
verifies on the target repo, this ensures no agent PR merges without: green
TypeScript build+test, green Python worker, a buildable image, and a passing mock
eval.

## Local parity

The same checks run locally: `pnpm -r build && pnpm -r test`, and for the worker
`cd worker && pip install -e .[dev] && ruff check . && pytest`. Keeping CI thin
and mirroring local commands means a green local run predicts a green CI run.
