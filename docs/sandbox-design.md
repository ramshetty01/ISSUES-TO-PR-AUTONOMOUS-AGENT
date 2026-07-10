# Sandbox Design

The worker executes attacker-influenced instructions (issue text) while holding
a live GitHub installation token and running arbitrary repository test suites.
Isolation is therefore the primary control, not an afterthought. This document
describes how the worker container is confined. It complements the
[safety policy](safety-policy.md), which covers in-process guardrails.

## Container isolation

The worker ships as a single image ([`worker/Dockerfile`](../worker/Dockerfile),
tag `itpr-worker:local`, built by
[`build-worker-image.sh`](../scripts/build-worker-image.sh)). Key properties:

- **Non-root.** The image creates and runs as UID `10001` (`worker`). Nothing in
  the job runs as root.
- **Minimal base.** `python:3.12-slim` plus only `git` and `ripgrep`. No compilers
  toolchain beyond what pip needs, no package managers left writable.
- **One job per container.** The dispatcher starts a fresh container per job and
  tears it down after, so no state leaks between runs. Resource caps
  (`--memory`, `--cpus`) are applied by the dispatcher's docker runner and by
  [`run-local-worker.sh`](../scripts/run-local-worker.sh).
- **Ephemeral filesystem.** Containers run `--rm`; the cloned repo and workspace
  vanish on exit.

## The workspace jail

All file tools operate through a path jail
([`worker/src/issue_to_pr_agent/safety/path_jail.py`](../worker/src/issue_to_pr_agent/safety/path_jail.py)).
Every read/write/edit path is resolved and must fall under `/workspace/<repo>`;
symlink escapes and `..` traversal are rejected. Writing outside the jail is a
[hard reject](safety-policy.md).

## Command execution

The `run_shell` and `run_tests` tools pass every command through the
[command denylist](../policies/command-denylist.yaml) before execution
(`safety/command_denylist.py`). Destructive patterns (`rm -rf /`, `mkfs`,
`curl … | sh`, raw-device writes) are refused. Commands run inside the container
with the same non-root user and the jailed working directory.

## Network posture

In local dev the container uses host networking so it can reach LocalStack and
Ollama. In a hardened deployment the container should run on an egress-filtered
network that permits only: the GitHub API, the configured LLM provider
endpoints, and the artifact store. Package installs during a run are constrained
by the bootstrap layer (`bootstrap/install_tools.py`) and the time budget
(`bootstrap/time_budget.py`).

## Credential handling

The installation token is short-lived (minted per run — see
[github-app-permissions.md](github-app-permissions.md)) and injected via env,
never written to the repo. The credential guard
(`safety/credential_guard.py`) and [log scrubber](safety-policy.md) prevent the
token — or any detected secret — from reaching commits, PR bodies, or stored
traces. Trace archives are additionally scrubbed on export by
[`scrub-trace-archives.py`](../scripts/scrub-trace-archives.py).

## Residual risk

Docker is not a strong multi-tenant boundary. For untrusted repositories at
scale, run each job in a microVM (Firecrawl/Firecracker or gVisor) — see
[cloud migration](cloud-migration.md) and
[residual risks](../security/threat-model/residual-risks.md).
