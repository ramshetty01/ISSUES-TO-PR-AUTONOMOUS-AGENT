# Threat Model — Attackers

Who might attack the agent, their capabilities, and their goals. See the
overview in [`docs/threat-model.md`](../../docs/threat-model.md).

## A1 — External issue author (untrusted, unauthenticated to the org)

- **Capability:** Can open an issue on a public repo and write arbitrary text in
  the title/body. Cannot apply the trigger label without maintainer action
  (labels are the gate — see
  [`policies/allowed-labels.yaml`](../../policies/allowed-labels.yaml)).
- **Goal:** Prompt-inject the agent into leaking the installation token, editing
  CI, or running attacker code; or trick a maintainer into labeling a poisoned
  issue.

## A2 — Malicious repository (untrusted code)

- **Capability:** Controls the repository the agent clones — tests, build
  scripts, `conftest.py`, git hooks, dependency manifests that execute on
  install.
- **Goal:** Achieve code execution in the worker, escape the sandbox, read the
  token from the environment, or exfiltrate data over the network.

## A3 — Malicious/compromised commenter with label rights

- **Capability:** A collaborator who can apply the `agent-fix` label and steer the
  agent via comments.
- **Goal:** Weaponize the agent's write access to push unreviewed changes, or
  drive it toward a forbidden action.

## A4 — Compromised LLM provider or model output

- **Capability:** Returns adversarial tool-call suggestions (e.g., "run this
  command", "commit this file").
- **Goal:** Induce a guardrail bypass. Mitigated because the LLM is never trusted
  as authority — every suggested action is re-checked by the safety layer.

## A5 — Insider / misconfiguration

- **Capability:** An operator who weakens policy (loosens the denylist, disables
  branch protection) or leaks `.env`.
- **Goal:** Not always malicious, but expands the blast radius. Out of primary
  scope, but the system fails closed to reduce accidental exposure.

## A6 — Network adversary

- **Capability:** Observes or tampers with traffic, replays webhook deliveries.
- **Goal:** Forge a webhook, replay an old delivery, or MITM provider/GitHub
  traffic. Countered by HMAC signature verification and replay protection.

See [assets](assets.md) for what these attackers target and
[attack paths](attack-paths.md) for concrete sequences.
