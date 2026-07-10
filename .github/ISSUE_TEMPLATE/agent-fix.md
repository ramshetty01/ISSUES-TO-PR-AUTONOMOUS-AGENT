---
name: Agent fix request
about: Ask the autonomous agent to open a PR that fixes a well-scoped issue
title: "[agent-fix] "
labels: ["agent-fix"]
assignees: []
---

<!--
Keep the ONE `agent-fix` label on this issue — it is the trigger the GitHub App
watches (see policies/allowed-labels.yaml). The agent works best on small,
verifiable changes. See docs/safety-policy.md for what it will refuse to do.
-->

## What is broken / needed

<!-- A clear, single-responsibility description. One fix per issue. -->

## How to reproduce (if a bug)

```
# commands / failing test / input that triggers the problem
```

## Expected behavior

<!-- What "fixed" looks like. If a specific test should pass, name it. -->

## Acceptance criteria

- [ ] <!-- e.g. `pytest tests/test_add.py` passes -->
- [ ] No changes outside the affected module(s)
- [ ] No new dependencies unless justified below

## Constraints / hints (optional)

<!--
Files likely involved, APIs to avoid, style notes. The agent honors the repo
policy (max diff size, forbidden paths) in policies/default-repo-policy.yaml.
-->
