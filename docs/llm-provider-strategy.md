# LLM Provider Strategy

The agent is designed to run at (near) zero cost by leaning on free-tier LLM
providers, with a deterministic fallback chain so a single provider's outage or
quota exhaustion never stalls a run. Providers and their caps are declared in
[`policies/llm-provider-limits.yaml`](../policies/llm-provider-limits.yaml);
an example operator config is
[`examples/llm-providers.example.yaml`](../examples/llm-providers.example.yaml).

## Providers

| Provider | Env key | Role | Notes |
| --- | --- | --- | --- |
| `nvidia_nim` | `NVIDIA_NIM_API_KEY` | Free-tier hosted | Strong coding models, generous tpm |
| `gemini` | `GEMINI_API_KEY` | Free-tier hosted | Large context, high daily token budget |
| `groq` | `GROQ_API_KEY` | Free-tier hosted | Very fast; tighter tpm |
| `ollama` | `OLLAMA_HOST` | Local | `qwen2.5-coder` via [`setup-ollama.sh`](../scripts/setup-ollama.sh); unlimited, private |
| `mock` | — | Always available | Canned responses; zero tokens, used by the [smoke eval](ci-verification-gates.md) and tests |

## Fallback order

The order is configured via `LLM_PROVIDER_ORDER` (default
`nvidia_nim,gemini,groq,ollama,mock`) and honored by the worker's router
([`worker/src/issue_to_pr_agent/llm/router.py`](../worker/src/issue_to_pr_agent/llm/router.py)).
It is tried left to right; the first **healthy and under-limit** provider serves
the request. `mock` is always last so the stack works with **zero API keys** —
critical for CI and for a first-run clone.

A provider is skipped for a request when: its API key is absent, it is rate- or
quota-limited (see below), or a call fails transiently (the router advances to
the next provider rather than failing the run).

## Rate limits

Free tiers publish three caps, mirrored in the policy file: requests/minute
(`rpm`), tokens/minute (`tpm`), and tokens/day (`daily`); `0` means unlimited
(local providers). The worker's rate limiter (`llm/rate_limiter.py`) enforces
these client-side to avoid provider-side 429s. Representative values:

| Provider | rpm | tpm | daily |
| --- | --- | --- | --- |
| nvidia_nim | 40 | 60000 | unlimited |
| gemini | 15 | 1000000 | 1500000 |
| groq | 30 | 6000 | 500000 |
| ollama / mock | unlimited | unlimited | unlimited |

## Rate limits vs budget

Provider rate limits protect the **provider**; the per-repo
[budget policy](budget-policy.md) protects the **operator** (tokens/day per
repo). Both apply. A run can be inside every provider's rate limit yet still be
denied by the repo's daily token cap.

## Choosing a model

For code edits the strategy favors capable coding models (NIM/Gemini) first for
quality, falling back to Groq for speed and Ollama for privacy/offline, with
`mock` as the always-on floor. See the model ablation runner
([`eval/runners/run_model_ablation.py`](../eval/runners/run_model_ablation.py))
and [eval methodology](eval-methodology.md) for how provider/model choices are
compared.
