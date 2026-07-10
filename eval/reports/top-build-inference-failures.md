# Top build/inference failures

Recurring failure modes observed when inferring how to build and test an unseen
repo, with the mitigation each drove.

1. **Missing/ambiguous package manager** — lockfile present but command unknown.
   → package-manager detector keys off lockfiles (`pnpm-lock.yaml`, `uv.lock`, …).
2. **No Dockerfile** — cannot containerize the test run.
   → Dockerfile synthesizer (see `dockerfile-synthesis-improvements.md`).
3. **Unknown CI command** — CI invokes a script the agent can't map to a runner.
   → language/test-command detector with a per-stack fallback matrix.
4. **Flaky tests** — unseeded randomness / time. → detected and reported, not
   "fixed" by loosening assertions.
5. **Coverage regression** — a fix that drops coverage below the gate is rejected
   by the verification stage.
