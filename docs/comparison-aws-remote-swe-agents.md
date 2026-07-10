# Comparison: AWS / hosted remote SWE agents

A design-level comparison against hosted remote software-engineering agents
(e.g. AWS-hosted offerings), from public documentation — not a reproduced
benchmark.

| Dimension | This agent | Hosted remote SWE agents |
|---|---|---|
| Infra | LocalStack locally → AWS in prod, **same code path** | managed cloud |
| Cost floor | $0 (free-tier LLMs + local) | per-seat / per-token |
| Data residency | self-hosted; traces never leave your infra | vendor-hosted |
| Safety gate | hard refusals + branch-protection precondition | varies |
| Budgets | token + $ caps per repo | usually $ only |
| Extensibility | open modules (worker/apps/packages) | closed |

**Cloud migration.** Because the worker/dispatcher speak the AWS SDK against a
swappable endpoint, moving from LocalStack to real AWS is an endpoint + IAM
change, not a rewrite — see [cloud-migration.md](./cloud-migration.md).

**Takeaways.** The trade is operational ownership for cost and control: you run
the stack, but you pay nothing per run, keep all data, and can audit every
decision. See [architecture.md](./architecture.md) and
[comparison-cursor-background-agents.md](./comparison-cursor-background-agents.md).
