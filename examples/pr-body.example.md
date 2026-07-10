## What

Guard parse() against None before dereferencing its value.

## Why

Closes #7 — parser crashes on None input. Approach: Guard parse() against None before dereferencing its value.

## Changes

- `src/parser.py` (modified, +4/-2)
- `tests/test_parser.py` (added, +2/-0)

## Verification

pytest worker/tests: 12 passed, 0 failed

Coverage: +1.2% (81.4% → 82.6%)

## Trace

[Langfuse trace `run-3f2a`](http://localhost:3000/trace/run-3f2a)

---
🤖 Opened automatically by the issue-to-PR agent.
