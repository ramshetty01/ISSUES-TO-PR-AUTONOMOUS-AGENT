# Threat Model — Assets

What has value and must be protected. Ranked roughly by impact if compromised.
See [attackers](attackers.md) and [mitigations](mitigations.md).

## AS1 — GitHub App installation token

The crown jewel. A short-lived, installation-scoped token with Contents/Issues/
Pull-requests write on the target repo. If leaked, an attacker can push code and
open PRs as the app for up to ~1 hour. Protected by: never placing it in LLM
context, the credential guard, secret scanning of all outputs, and its short
lifetime (see
[`docs/github-app-permissions.md`](../../docs/github-app-permissions.md)).

## AS2 — GitHub App private key & webhook secret

`GITHUB_APP_PRIVATE_KEY` mints tokens for **every** installation;
`GITHUB_WEBHOOK_SECRET` authenticates deliveries. Compromise is catastrophic and
long-lived. Stored only in `.env` / secret manager, never in the repo, never in
traces.

## AS3 — The target repository's integrity

The ability to merge code. Protected in depth: the agent can only propose PRs
(never push to a protected branch), and branch protection + human review +
[CI gates](../../docs/ci-verification-gates.md) stand between a proposal and
`main`.

## AS4 — CI/CD execution

`.github/workflows/**` runs with repository secrets and elevated tokens.
Editing a workflow is a direct path to persistent compromise, so it is a
[hard reject](../../docs/safety-policy.md) and the App has no Actions permission.

## AS5 — LLM provider credentials & quota

`NVIDIA_NIM_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`. Leakage enables free use
of the operator's quota; abuse can exhaust it (DoS). Protected by secret scanning
and the [budget policy](../../docs/budget-policy.md) / rate limiter.

## AS6 — Run artifacts & traces

Stored in S3. May incidentally capture secrets or PII from repo content or issue
text. Protected by the [log scrubber](../../docs/safety-policy.md) at write time
and by [`scrub-trace-archives.py`](../../scripts/scrub-trace-archives.py) at
export time.

## AS7 — The worker host / other tenants

The machine running the container and any co-located jobs. A sandbox escape
threatens confidentiality and integrity beyond the current job. Protected by the
non-root, resource-capped, ephemeral container ([sandbox](../../docs/sandbox-design.md)).

## AS8 — Operator budget (money)

Even with free tiers, paid fallbacks and compute cost money. Bounded per repo by
the daily dollar cap.
