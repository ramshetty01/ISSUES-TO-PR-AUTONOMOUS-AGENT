# Comparison: Cursor background agents

A design-level comparison against Cursor's background agents, drawn from public
documentation — not a reproduced benchmark.

| Dimension | This agent | Cursor background agents |
|---|---|---|
| Trigger | GitHub issue label / PR comment (webhook) | editor / cloud task |
| Cost model | $0 free-tier + local (Ollama) | subscription / usage |
| Isolation | per-run Docker sandbox, workspace jail, non-root | cloud sandbox |
| Safety boundary | hard refusals: forbidden paths, secrets, force-push, budget | proprietary |
| Budgets | token **and** dollar caps, enforced even at $0 | usage-based |
| Observability | self-hosted Langfuse traces + redacted archives | vendor dashboard |
| Portability | LocalStack → AWS, same code path | vendor-hosted |

**Takeaways.** The differentiators here are the **$0 free-tier posture**, an
explicit **hard safety boundary** ([safety-policy.md](./safety-policy.md)), and
**local-first, self-hosted observability**. Cursor optimizes for tight
editor-integrated iteration; this agent optimizes for auditable, budget-bounded,
self-hostable automation. See also
[comparison-aws-remote-swe-agents.md](./comparison-aws-remote-swe-agents.md).
