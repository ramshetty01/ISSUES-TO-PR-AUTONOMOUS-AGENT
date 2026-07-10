# Internal eval harness

A seeded-issue harness that scores the agent end-to-end across stacks
(python / node / go / rust / mixed) with **free or zero-token** providers.

## Layout
- `seeded-issues/` — the issue corpus (`issues.json` manifest + per-stack `*.md`).
- `runners/` — `run_single_issue.py`, `run_internal_eval.py` (`--subset`,
  `--resume`), `run_model_ablation.py`, `aggregate_results.py`.
- `metrics/` — `pass_rate`, `pr_quality`, `diff_size`, `coverage_delta`,
  `style_conformance`, `cost_latency`, `safety_score`, `operator_ux_score`.
- `results/` — generated JSON + `final-scorecard.md`.
- `reports/` — written analysis (`eval-report`, `comparison-report`,
  `top-build-inference-failures`, `dockerfile-synthesis-improvements`).
- `fixtures/` — public repo fixtures (unlimited free GitHub Actions).

## Zero-token smoke path
```bash
python3 eval/runners/run_single_issue.py --provider mock --issue issue-001-null-input
python3 eval/runners/run_internal_eval.py --provider mock --subset smoke
# or:
make eval
```
The `mock` provider is a deterministic simulation — no keys, no tokens — so the
whole pipeline (solve → diff → PR body → run summary → metrics) is exercised
offline. It includes an adversarial issue (`issue-014-forbidden-edit`) whose
**correct** outcome is a safety **refusal**, not a PR.

## Rate-limit resilience
Free providers throttle. `run_internal_eval.py --resume` reuses results already
written, so a run interrupted mid-way can be re-invoked and continue.

## Model ablation
```bash
python3 eval/runners/run_model_ablation.py --providers mock,gemini,ollama --subset smoke
```
Compares free providers on a subset; writes `results/model-ablation.json`.
