# Threat Model — Residual Risks

Risks that remain after the [mitigations](mitigations.md), why they are accepted
for this reference implementation, and how to harden them for production.

## R1 — Docker is not a strong isolation boundary

The worker runs in a non-root, capped, ephemeral container, but a container is
not a security boundary against a determined kernel exploit. A malicious
repository ([A2](attackers.md)) that achieves code execution could, in
principle, attempt a container escape.

- **Accepted because:** for trusted/first-party repos the risk is low, and Docker
  keeps local dev friction near zero.
- **Harden by:** running each job in a microVM (Firecracker/Kata) or gVisor,
  one-per-job, with no shared kernel. See
  [cloud migration](../../docs/cloud-migration.md).

## R2 — Regex-based secret detection has gaps

`secret_scanner.py` matches known token shapes. A novel or custom secret format,
or a secret split across lines, can evade it.

- **Accepted because:** it covers the common high-value formats (GitHub, AWS,
  Slack, Google, PEM, bearer, generic `key=value`) and is regression-tested.
- **Harden by:** adding entropy-based detection and provider-specific verifiers,
  and treating the token as tainted end-to-end so it can never reach an output
  path regardless of format.

## R3 — Prompt injection is an evolving problem

Guardrails are code/policy, not prompt, so injection cannot bypass a hard reject.
But injection can still waste budget or steer the agent toward low-value or
subtly wrong changes within the allowed envelope.

- **Accepted because:** the blast radius is bounded (PR-only, reviewed, budgeted)
  and a human approves every merge.
- **Harden by:** input classification/sanitization of issue text and stricter
  change-intent validation against the stated acceptance criteria.

## R4 — Egress is open in local dev

The dev container uses host networking to reach LocalStack/Ollama, so a
compromised run could reach arbitrary hosts.

- **Accepted because:** local dev only, on the operator's own machine.
- **Harden by:** an allowlist egress proxy in production (GitHub + providers +
  artifact store only), which also blocks the AP3 reverse-shell.

## R5 — Supply chain (dependencies)

The worker `pip install`s repo dependencies to run tests; a malicious manifest
can execute code at install time.

- **Accepted because:** it is contained by the sandbox (R1) and time budget.
- **Harden by:** installing in an even more restricted step, pinning/hashing,
  and disabling network during dependency resolution where feasible.

## R6 — Operator misconfiguration

Weakening a policy file, disabling branch protection, or leaking `.env` expands
the blast radius. Outside the primary trust model, but the system fails closed to
limit accidental exposure.

- **Harden by:** treating [`policies/`](../../policies) as reviewed,
  version-controlled config and keeping secrets in a manager, not on disk.

These residual risks are intentionally documented rather than hidden; see the
overview in [`docs/threat-model.md`](../../docs/threat-model.md) and the
disclosure process in [`../SECURITY.md`](../SECURITY.md).
