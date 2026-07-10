# Comparison report (design-level)

A design-level comparison againstpublished autonomous-PR systems, drawn from public
docs — not a head-to-head benchmark (their harnesses are not reproducible here).

| Dimension | This agent | Typical hosted agent |
|---|---|---|
| Cost floor | $0 (free-tier + local) | per-token / seat |
| Safety gate | hard refusals (forbidden paths, secrets, force-push) | varies |
| Budgets | token + $ caps, enforced even at $0 | usually $ only |
| Observability | self-hosted Langfuse traces + redacted archives | vendor-hosted |
| Portability | LocalStack → AWS, same code path | vendor lock-in |

The differentiators are the **$0 free-tier posture**, the **hard safety
boundary**, and **local-first observability**.
