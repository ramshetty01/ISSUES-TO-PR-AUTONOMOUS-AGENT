# Eval methodology

The internal eval scores the agent end-to-end on a seeded corpus of issues
across stacks (python / node / go / rust / mixed). See the runnable harness in
[`eval/`](../eval/README.md).

## Corpus
Seeded issues live in `eval/seeded-issues/` with an `issues.json` manifest. Each
issue declares its stack, difficulty, and **expected outcome** — a pull request,
or (for adversarial issues) a **safety refusal**. Fixtures are hosted as public
GitHub repos for unlimited free Actions.

## Metrics
Eight metrics (`eval/metrics/`): `pass_rate`, `pr_quality`, `diff_size`,
`coverage_delta`, `style_conformance`, `cost_latency` (tokens + wall-clock),
`safety_score`, `operator_ux_score`. A correct refusal on an adversarial issue
scores full marks on safety.

## Runners
- `run_single_issue.py` — one issue, one provider.
- `run_internal_eval.py` — the corpus, with `--subset smoke|full` and `--resume`
  (survives free-tier rate-limit interruptions).
- `run_model_ablation.py` — compares free providers on a subset.
- `aggregate_results.py` — merges results into a scorecard.

## Zero-token path
The `mock` provider deterministically simulates the agent's output so the whole
pipeline runs offline and in CI on every PR ($0, 0 tokens). Real-provider runs
populate the same schema. See [llm-provider-strategy.md](./llm-provider-strategy.md)
and the design-level [comparison reports](./comparison-cursor-background-agents.md).
