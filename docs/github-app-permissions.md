# GitHub App Permissions

The agent authenticates as a GitHub App and operates with short-lived
**installation tokens**, never a personal access token. This document lists the
minimal permission set, why each scope is needed, and how tokens are handled.
Set the App up with [`setup-github-app.sh`](../scripts/setup-github-app.sh); a
reference manifest is in
[`examples/github-app-manifest.example.json`](../examples/github-app-manifest.example.json).

## Repository permissions

| Scope | Level | Why |
| --- | --- | --- |
| Contents | Read & write | Clone the repo, create a branch, push commits with the fix |
| Issues | Read & write | Read the triggering issue; post the ack and result comments |
| Pull requests | Read & write | Open the fix PR and read its file list for verification |
| Metadata | Read-only | Mandatory for every App |
| Administration | Read-only | Read branch-protection settings for the [protection gate](branch-protection-requirements.md) |

The App requests **no** organization permissions and **no** write access to
Administration — it can *read* protection rules but never *change* them. It has
no access to Actions/workflows, matching the [safety policy](safety-policy.md)
hard reject on editing `.github/workflows/**`.

## Subscribed events

- **Issues** — fires when a maintainer applies the `agent-fix` label
  ([`allowed-labels.yaml`](../policies/allowed-labels.yaml)).
- **Issue comment** — lets a maintainer re-trigger or provide guidance.
- **Pull request** — track the status of PRs the agent opened.

## Token lifecycle

1. The App holds an App ID and a private key (`.pem`), stored as
   `GITHUB_APP_ID` and `GITHUB_APP_PRIVATE_KEY` in `.env`.
2. Per job, the code mints an **installation token**
   ([`packages/github-client/src/auth.ts`](../packages/github-client/src/auth.ts))
   scoped to the single installation. These expire in ~1 hour.
3. The token is injected into the worker via env, used inside the
   [sandbox](sandbox-design.md), and never written to disk in the repo or into
   commit/PR content. The credential guard + [log scrubber](safety-policy.md)
   prevent leakage; exported traces are re-scrubbed by
   [`scrub-trace-archives.py`](../scripts/scrub-trace-archives.py).

## Webhook verification

Every delivery is verified before it is trusted: HMAC-SHA256 signature check
against `GITHUB_WEBHOOK_SECRET`, replay protection on the delivery id, and
payload sanitization (`apps/github-app/src/security/`). In local dev, deliveries
are forwarded through a smee.io channel created by
[`setup-smee.sh`](../scripts/setup-smee.sh); the `SMEE_URL` is the App's webhook
URL.

## Least privilege in practice

Because the token is installation-scoped and short-lived, a compromised run can
at worst act within that one repo for under an hour, and cannot touch CI,
secrets, or protected-branch settings. See the
[threat model](threat-model.md) for the full analysis.
