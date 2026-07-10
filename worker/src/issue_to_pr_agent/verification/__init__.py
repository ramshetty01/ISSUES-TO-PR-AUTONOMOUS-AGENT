"""Verification gates: tests, coverage, style, forbidden diffs, diff size, verdict."""

from .test_result import TestResult
from .junit_parser import parse_junit
from .coverage import Coverage
from .coverage_py_parser import parse_coverage_py
from .jacoco_parser import parse_jacoco
from .coverage_delta import CoverageDelta, coverage_delta
from .ci_runner import run_tests
from .full_test_suite import run_full_suite
from .flaky_test_detector import detect_flaky
from .style_check import StyleResult, run_style_check
from .forbidden_diff_check import (
    ForbiddenDiffResult,
    changed_paths_from_diff,
    check_forbidden_diff,
    check_forbidden_paths,
    load_forbidden_paths,
)
from .diff_size_check import DiffSizeResult, DiffStats, check_diff_size, diff_stats
from .verdict import Verdict
from .final_gate import final_gate

__all__ = [
    "TestResult",
    "parse_junit",
    "Coverage",
    "parse_coverage_py",
    "parse_jacoco",
    "CoverageDelta",
    "coverage_delta",
    "run_tests",
    "run_full_suite",
    "detect_flaky",
    "StyleResult",
    "run_style_check",
    "ForbiddenDiffResult",
    "changed_paths_from_diff",
    "check_forbidden_diff",
    "check_forbidden_paths",
    "load_forbidden_paths",
    "DiffSizeResult",
    "DiffStats",
    "check_diff_size",
    "diff_stats",
    "Verdict",
    "final_gate",
]
