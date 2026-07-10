"""Phase 26 coverage + flaky-test tests."""

from __future__ import annotations

from issue_to_pr_agent.verification.coverage import Coverage
from issue_to_pr_agent.verification.coverage_delta import coverage_delta
from issue_to_pr_agent.verification.coverage_py_parser import parse_coverage_py
from issue_to_pr_agent.verification.jacoco_parser import parse_jacoco
from issue_to_pr_agent.verification.flaky_test_detector import detect_flaky
from issue_to_pr_agent.verification.test_result import TestResult

COVERAGE_PY_XML = """<?xml version="1.0"?>
<coverage line-rate="0.85">
  <packages><package><classes>
    <class filename="calc.py"><lines>
      <line number="1" hits="1"/>
      <line number="2" hits="0"/>
    </lines></class>
  </classes></package></packages>
</coverage>
"""

JACOCO_XML = """<?xml version="1.0"?>
<report>
  <counter type="LINE" missed="20" covered="80"/>
</report>
"""


def test_coverage_py_parse() -> None:
    cov = parse_coverage_py(COVERAGE_PY_XML)
    assert cov.percent == 85.0
    assert cov.per_file["calc.py"] == 50.0


def test_jacoco_parse() -> None:
    cov = parse_jacoco(JACOCO_XML)
    assert cov.percent == 80.0
    assert cov.covered_lines == 80 and cov.total_lines == 100


def test_coverage_delta_regression() -> None:
    d = coverage_delta(Coverage(percent=90.0), Coverage(percent=88.0))
    assert d.regressed is True
    assert d.delta == -2.0


def test_coverage_delta_improvement_ok() -> None:
    d = coverage_delta(Coverage(percent=80.0), Coverage(percent=82.0))
    assert d.regressed is False


def test_coverage_delta_within_tolerance() -> None:
    d = coverage_delta(Coverage(percent=80.0), Coverage(percent=79.995))
    assert d.regressed is False  # tiny float noise not a regression


def test_flaky_detector_passes_on_retry() -> None:
    outcomes = [TestResult(failed=1), TestResult(passed=3)]
    result, flaky = detect_flaky(lambda: outcomes.pop(0), retries=2)
    assert result.ok is True
    assert flaky is True


def test_flaky_detector_real_failure() -> None:
    result, flaky = detect_flaky(lambda: TestResult(failed=1), retries=2)
    assert result.ok is False
    assert flaky is False
