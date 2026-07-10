# Safety Policy

The worker treats issue text and repository contents as untrusted. On top of the
container [sandbox](sandbox-design.md), it enforces an in-process safety layer
([`worker/src/issue_to_pr_agent/safety/`](../worker/src/issue_to_pr_agent/safety))
that inspects every tool call and every artifact before it leaves the process.
The rules are declared as data in [`policies/`](../policies), so they can be
audited and tuned without touching code.

## Hard rejects

Some conditions cause an immediate, non-negotiable refusal
([`policies/safety-hard-rejects.yaml`](../policies/safety-hard-rejects.yaml)).
The run aborts, the reason is recorded, and no PR is opened:

- Editing CI/workflow files (`.github/workflows/**`, `.github/actions/**`) —
  enforced by `workflow_write_blocker.py`.
- Force-pushing, or pushing to a protected branch (`main`, `master`) —
  `no_force_push.py`.
- Committing a detected secret or private key — `secret_scanner.py` /
  `credential_guard.py`.
- Running a command on the [denylist](../policies/command-denylist.yaml) —
  `command_denylist.py`.
- Writing outside the workspace jail — `path_jail.py`.

Each rejection funnels through `refusal.py`, producing a structured refusal that
the finalizer surfaces on the issue rather than silently dropping.

## Forbidden paths

Beyond workflows, the agent must never modify the paths in
[`policies/forbidden-paths.yaml`](../policies/forbidden-paths.yaml) (`.git/`,
`.env`, `secrets/`). `forbidden_paths.py` checks proposed edits and the final
diff. A change touching any of these fails both the safety layer and the
[CI verification gates](ci-verification-gates.md).

## Secret & PII redaction

Two scanners back the redaction layer:

- **Secrets** (`secret_scanner.py`): GitHub tokens/PATs, AWS keys, Slack tokens,
  Google API keys, bearer tokens, PEM private keys, and generic
  `key: value` secrets.
- **PII** (`pii_scanner.py`): emails, IPv4 addresses, phone numbers.

`log_scrubber.py` replaces any match with `[REDACTED:<kind>]` — idempotently, so
placeholders never re-match. The standalone
[`scrub-trace-archives.py`](../scripts/scrub-trace-archives.py) mirrors these
patterns for exported traces. Test vectors that must redact live in
[`security/secret-redaction-test-cases.json`](../security/secret-redaction-test-cases.json)
and
[`security/pii-redaction-test-cases.json`](../security/pii-redaction-test-cases.json).
Illustrative inputs the layer must reject are in
[`security/forbidden-diff-examples/`](../security/forbidden-diff-examples).

## Verification before PR

The agent does not open a PR just because it produced a diff. The finalizer
requires: tests pass (or the issue's stated acceptance criterion is met), the
diff is within the repo policy size limits
([`default-repo-policy.yaml`](../policies/default-repo-policy.yaml)), no forbidden
paths are touched, and no secret is present. Only then does it call the GitHub
API. See the [budget policy](budget-policy.md) for the spend guardrail that runs
in parallel and the [threat model](threat-model.md) for the adversary this
defends against.
