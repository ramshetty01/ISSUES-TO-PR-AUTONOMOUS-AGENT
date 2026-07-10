<!--
Thanks for the PR. If this PR was opened by the autonomous agent, the sections
below are filled from the run summary (see examples/pr-body.example.md). Human
contributors: fill them in yourself.
-->

## What & why

<!-- What this changes and the issue it addresses. -->

Closes #

## How it was verified

<!-- Tests run, commands, before/after. The agent attaches the run summary here. -->

```
```

## Change surface

- Files changed:
- Lines changed:
- New dependencies: none <!-- or list + justify -->

## Safety checklist

- [ ] No changes under `.github/workflows/**` or other forbidden paths (policies/forbidden-paths.yaml)
- [ ] No secrets, tokens, or private keys in the diff or logs
- [ ] No force-push / no direct push to a protected branch
- [ ] Diff size within repo policy (policies/default-repo-policy.yaml)
- [ ] CI is green (TypeScript build+test, Python worker, mock eval)

<!--
See docs/ci-verification-gates.md for what CI enforces and
docs/safety-policy.md for the hard rejects the agent applies before it ever
opens a PR.
-->
