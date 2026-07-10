"""Phase 26 forbidden-diff + diff-size + final-gate tests."""

from __future__ import annotations

from pathlib import Path

from issue_to_pr_agent.verification import (
    changed_paths_from_diff,
    check_diff_size,
    check_forbidden_diff,
    final_gate,
    load_forbidden_paths,
    parse_junit,
)
from issue_to_pr_agent.verification.coverage import Coverage
from issue_to_pr_agent.verification.coverage_delta import coverage_delta
from issue_to_pr_agent.verification.test_result import TestResult

WORKFLOW_DIFF = """diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index 111..222 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -1 +1 @@
-name: ci
+name: pwned
"""

SAFE_DIFF = """diff --git a/src/calc.py b/src/calc.py
index 111..222 100644
--- a/src/calc.py
+++ b/src/calc.py
@@ -1,2 +1,2 @@
-def add(a, b): return a - b
+def add(a, b): return a + b
"""


def test_changed_paths_parsed() -> None:
    assert changed_paths_from_diff(WORKFLOW_DIFF) == [".github/workflows/ci.yml"]
    assert changed_paths_from_diff(SAFE_DIFF) == ["src/calc.py"]


def test_workflow_edit_is_rejected() -> None:
    res = check_forbidden_diff(WORKFLOW_DIFF)
    assert res.ok is False
    assert ".github/workflows/ci.yml" in res.violations


def test_safe_edit_allowed() -> None:
    assert check_forbidden_diff(SAFE_DIFF).ok is True


def test_load_forbidden_paths_policy() -> None:
    policy = Path(__file__).resolve().parents[2] / "policies" / "forbidden-paths.yaml"
    forbidden = load_forbidden_paths(policy)
    assert ".github/workflows/" in forbidden
    assert check_forbidden_diff(WORKFLOW_DIFF, forbidden).ok is False


def test_diff_size_cap() -> None:
    big = "diff --git a/x b/x\n" + "\n".join(f"+line{i}" for i in range(600))
    res = check_diff_size(big, max_lines=500)
    assert res.ok is False
    assert "changed lines" in res.reason
    assert check_diff_size(SAFE_DIFF).ok is True


def test_final_gate_blocks_forbidden_and_failing() -> None:
    tests_ok = TestResult(passed=5)
    gate_ok = final_gate(
        tests=tests_ok,
        forbidden=check_forbidden_diff(SAFE_DIFF),
        diff_size=check_diff_size(SAFE_DIFF),
    )
    assert gate_ok.passed is True

    gate_bad = final_gate(
        tests=TestResult(failed=1),
        forbidden=check_forbidden_diff(WORKFLOW_DIFF),
        diff_size=check_diff_size(SAFE_DIFF),
    )
    assert gate_bad.passed is False
    assert gate_bad.checks["tests"] is False
    assert gate_bad.checks["forbidden_paths"] is False


def test_final_gate_blocks_coverage_regression() -> None:
    delta = coverage_delta(Coverage(percent=90.0), Coverage(percent=80.0))
    gate = final_gate(
        tests=TestResult(passed=1),
        forbidden=check_forbidden_diff(SAFE_DIFF),
        diff_size=check_diff_size(SAFE_DIFF),
        coverage=delta,
    )
    assert gate.passed is False
    assert gate.checks["coverage"] is False


def test_junit_parse() -> None:
    xml = (
        '<testsuite tests="3" failures="1" errors="0" skipped="0">'
        '<testcase name="a"/>'
        '<testcase name="b"><failure message="boom"/></testcase>'
        '<testcase name="c"/></testsuite>'
    )
    r = parse_junit(xml)
    assert r.passed == 2 and r.failed == 1 and r.ok is False
    assert any("boom" in f for f in r.failures)
