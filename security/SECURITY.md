# Security Policy

`issue-to-pr-agent` executes attacker-influenced input while holding a GitHub
token, so we take security reports seriously and appreciate responsible
disclosure.

## Supported versions

This is a reference implementation; security fixes are applied to the `main`
branch and the most recent tagged release.

## Reporting a vulnerability

**Do not open a public issue for security vulnerabilities.**

Instead, use GitHub's private vulnerability reporting for this repository
(Security tab → "Report a vulnerability"), or email the maintainers listed in the
repository metadata. Please include:

- A description of the vulnerability and its impact.
- Steps to reproduce (a minimal issue payload, diff, or command sequence).
- Affected component: github-app, dispatcher, worker, dashboard, packages, or
  CI/scripts.
- Any suggested mitigation.

If your report involves a token, secret, or PII, **redact it first** with
`python3 scripts/scrub-trace-archives.py --pii <file>`.

## What to expect

- Acknowledgement within 3 business days.
- An initial assessment and severity rating within 7 business days.
- Coordinated disclosure once a fix is available; we will credit you unless you
  prefer to remain anonymous.

## Scope

In scope: prompt-injection leading to a guardrail bypass, sandbox escape,
credential/secret leakage, CI-workflow tampering, budget-gate bypass, and
webhook signature/replay weaknesses.

Out of scope: findings that require a maintainer to intentionally misconfigure
policy, denial of service against your own quota, and issues in third-party
dependencies (report those upstream, though we welcome a heads-up).

## Design references

The security architecture is documented in
[`docs/threat-model.md`](../docs/threat-model.md),
[`docs/safety-policy.md`](../docs/safety-policy.md), and
[`docs/sandbox-design.md`](../docs/sandbox-design.md). The detailed threat model
lives alongside this file in [`threat-model/`](threat-model). Redaction test
vectors are in
[`secret-redaction-test-cases.json`](secret-redaction-test-cases.json) and
[`pii-redaction-test-cases.json`](pii-redaction-test-cases.json); illustrative
inputs the safety layer must reject are in
[`forbidden-diff-examples/`](forbidden-diff-examples).
