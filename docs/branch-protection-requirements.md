# Branch Protection Requirements

Before the agent will operate on a repository, that repo's default branch must
be protected. This is a hard prerequisite: it guarantees the agent's work always
lands through a reviewable PR and can never bypass review or overwrite history,
even if a later bug or prompt-injection tried to. The requirement is declared in
[`policies/branch-protection-required.yaml`](../policies/branch-protection-required.yaml)
and enforced by the dispatcher's protection gate.

## Required settings

| Requirement | Policy key | Rationale |
| --- | --- | --- |
| Require pull requests before merging | `requirePullRequest: true` | The agent's changes must be reviewed, not pushed to the branch |
| At least one approving review | `minApprovals: 1` | A human signs off before merge |
| Disallow force pushes | `disallowForcePush: true` | History cannot be rewritten (matches the no-force-push [hard reject](safety-policy.md)) |
| Restrict direct pushes | `restrictDirectPush: true` | Everything goes through a PR, including the App |

The recommended required status check is **`ci-passed`** (see
[CI verification gates](ci-verification-gates.md)), and enabling "include
administrators" is advised so the rules apply universally.

## How the gate works

The dispatcher reads the live protection snapshot via
[`packages/github-client/src/protection.ts`](../packages/github-client/src/protection.ts)
(`getBranchProtection`, which maps GitHub's API response to a
`BranchProtectionSnapshot`) and compares it against the policy. If any
requirement is unmet, the job is **not** run: the issue is commented with the
specific gap, and the run is recorded as skipped. Requires only the
Administration: read-only permission (see
[github-app-permissions.md](github-app-permissions.md)).

## Verifying a repo before onboarding

Operators can check a repo without pushing a job through the queue:

```bash
pnpm dlx tsx scripts/verify-branch-protection.ts owner/repo
```

[`verify-branch-protection.ts`](../scripts/verify-branch-protection.ts) prints
the live snapshot and exits non-zero with a list of violations if protection is
missing or too weak — the same comparison the dispatcher performs.

## Failure mode

If a repository's protection is later weakened while a job is in flight, the
gate re-checks at dispatch time, so the weakening takes effect immediately. The
agent fails **closed**: no protection, no run. This is a core mitigation in the
[threat model](threat-model.md).
