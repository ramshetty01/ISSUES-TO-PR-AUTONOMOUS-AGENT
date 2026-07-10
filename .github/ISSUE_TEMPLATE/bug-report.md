---
name: Bug report
about: Report a defect in the issue-to-pr-agent itself (app, dispatcher, worker)
title: "[bug] "
labels: ["bug"]
assignees: []
---

<!--
This is for bugs in the agent platform, NOT a request for the agent to fix a
bug in your repo (use "Agent fix request" for that). Do NOT add the agent-fix
label here.
-->

## Summary

<!-- One or two sentences describing the defect. -->

## Component

- [ ] github-app (webhook receiver)
- [ ] dispatcher (queue / budget / runner)
- [ ] worker (agent loop / tools / safety)
- [ ] dashboard
- [ ] packages / shared
- [ ] eval / CI / scripts

## Steps to reproduce

1.
2.
3.

## Expected vs actual

**Expected:**

**Actual:**

## Logs / trace

<!--
Paste relevant logs. IMPORTANT: scrub secrets first — run
`python3 scripts/scrub-trace-archives.py --pii <file>` on any trace archive
before attaching. See docs/safety-policy.md.
-->

```
```

## Environment

- OS:
- Node / pnpm:
- Python:
- LLM provider order:
