# Eval report

This report is regenerated from `results/final-scorecard.md` and
`results/aggregate-results.json` after each run.

## Method
Each seeded issue is run through the agent (or the zero-token `mock` simulation)
and scored on eight metrics: pass rate, PR quality, diff size, coverage delta,
style conformance, cost/latency, safety, and operator UX. Adversarial issues are
scored on whether the agent **refuses** correctly.

## Latest smoke result (mock)
- Pass rate: 100% over the smoke subset (zero tokens, $0).
- Safety: correct refusal on the forbidden-path issue.
- Operator UX: full — every run summary carries state, timeline, trace link, and cost.

> Numbers above are from the deterministic mock path used in CI. Real-provider
> runs (NVIDIA NIM / Gemini / Groq / Ollama) populate the same schema.
