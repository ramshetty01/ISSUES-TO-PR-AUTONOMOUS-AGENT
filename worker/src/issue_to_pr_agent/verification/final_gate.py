"""Aggregate every check into a single pass/fail verdict."""

from __future__ import annotations

from .coverage_delta import CoverageDelta
from .diff_size_check import DiffSizeResult
from .forbidden_diff_check import ForbiddenDiffResult
from .style_check import StyleResult
from .test_result import TestResult
from .verdict import Verdict


def final_gate(
    *,
    tests: TestResult,
    forbidden: ForbiddenDiffResult,
    diff_size: DiffSizeResult,
    coverage: CoverageDelta | None = None,
    style: StyleResult | None = None,
) -> Verdict:
    v = Verdict(passed=True)
    v.record("tests", tests.ok, "" if tests.ok else "tests are failing")
    v.record(
        "forbidden_paths",
        forbidden.ok,
        "" if forbidden.ok else "edits forbidden paths: " + ", ".join(forbidden.violations),
    )
    v.record("diff_size", diff_size.ok, diff_size.reason)
    if coverage is not None:
        v.record(
            "coverage",
            not coverage.regressed,
            "" if not coverage.regressed else f"coverage regressed by {coverage.delta}%",
        )
    if style is not None:
        v.record("style", style.ok, "" if style.ok else "style check failed")
    v.passed = all(v.checks.values())
    return v
