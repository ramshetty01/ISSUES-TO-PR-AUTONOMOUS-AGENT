# Threat Model — Mitigations

The controls that break the [attack paths](attack-paths.md), grouped by layer.
Each is defense-in-depth: no single control is trusted alone, and every layer
fails closed.

## M1 — Input trust boundary

- Deny-by-default triggering: only issues with an allowed label
  ([`allowed-labels.yaml`](../../policies/allowed-labels.yaml)) and from allowed
  actors/repos are processed (github-app filters).
- Guardrails are **policy + code, never prompt** — the LLM cannot argue past
  them. Addresses AP1, AP2, A4.

## M2 — Credential isolation

- Installation-scoped, ~1h token; App private key and webhook secret live only in
  `.env`/secret manager.
- The token is never placed in LLM context; `credential_guard.py` +
  `secret_scanner.py` refuse to emit it. Addresses AP1, AS1–AS2.

## M3 — Safety hard rejects

Immediate, non-negotiable refusals
([`safety-hard-rejects.yaml`](../../policies/safety-hard-rejects.yaml)):
workflow edits (`workflow_write_blocker.py`), force-push/protected-branch push
(`no_force_push.py`), secret commit, denylisted command
(`command_denylist.py`), out-of-jail write (`path_jail.py`). Addresses AP2, AP4,
AP5.

## M4 — Forbidden paths

`.github/workflows/`, `.git/`, `.env`, `secrets/`
([`forbidden-paths.yaml`](../../policies/forbidden-paths.yaml)) are blocked on
edit and re-checked on the final diff (`forbidden_paths.py`). Addresses AP2.

## M5 — Sandbox

Non-root (UID 10001), minimal image, per-job ephemeral container with
`--memory`/`--cpus` caps, path jail, and (recommended) egress filtering. See
[sandbox design](../../docs/sandbox-design.md). Addresses AP3.

## M6 — Branch protection gate

The dispatcher verifies the target branch has required PR reviews, disallows
force-push, and restricts direct pushes before running
([branch-protection-requirements.md](../../docs/branch-protection-requirements.md)),
using read-only Administration permission. Fails closed. Addresses AP4, AS3.

## M7 — Budget & rate limiting

Per-repo daily token/dollar caps ([budget policy](../../docs/budget-policy.md))
enforced by an atomic reserve before each run; provider-side rate limiter and a
per-run time budget. Dispatcher fails closed if the ledger is unreachable.
Addresses AP6, AS5, AS8.

## M8 — Redaction

`log_scrubber.py` redacts secrets (and optionally PII) at write time;
[`scrub-trace-archives.py`](../../scripts/scrub-trace-archives.py) at export.
Vectors regression-tested by the `*-redaction-test-cases.json` files. Addresses
AP1, AP8, AS6.

## M9 — Webhook authenticity

HMAC-SHA256 signature verification + per-delivery replay protection + payload
sanitization (`apps/github-app/src/security/`). Addresses AP7.

## M10 — Independent CI re-verification

Every PR is re-checked by [CI](../../docs/ci-verification-gates.md) (TS
build+test, Python worker, image build, zero-token mock eval), and a human review
is required before merge. Catches anything the worker's self-verification missed.
Addresses AP2, AS3.
