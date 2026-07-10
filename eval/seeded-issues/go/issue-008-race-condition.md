# Data race on shared counter

**Stack:** go  **Difficulty:** 3/3  **Expected outcome:** pull request

## Description
Data race on shared counter. Reproduce, fix the root cause, and add or update a test that fails before the change and passes after.

## Acceptance
- A PR that fixes the bug, keeps the diff small, and does not touch forbidden paths.
- Verification (tests) passes; coverage does not regress.
