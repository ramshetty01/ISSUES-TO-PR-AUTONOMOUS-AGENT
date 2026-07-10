"""Re-run suspected-flaky tests: a failure that passes on retry is flaky."""

from __future__ import annotations

from collections.abc import Callable

from .test_result import TestResult


def detect_flaky(
    run: Callable[[], TestResult], *, retries: int = 2
) -> tuple[TestResult, bool]:
    """Run once; if it fails, retry. Returns (final_result, was_flaky).

    was_flaky is True when an initial failure later passed.
    """
    result = run()
    if result.ok:
        return result, False
    for _ in range(max(0, retries)):
        retry = run()
        if retry.ok:
            return retry, True
        result = retry
    return result, False
