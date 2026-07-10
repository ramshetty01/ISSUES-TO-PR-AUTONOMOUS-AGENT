"""Run the test command inside the sandbox and normalize the result.

If a JUnit XML report is produced, it is parsed; otherwise the exit code alone
determines pass/fail.
"""

from __future__ import annotations

from ..sandbox.base import Sandbox
from .junit_parser import parse_junit
from .test_result import TestResult


def run_tests(
    sandbox: Sandbox, command: str, *, junit_xml: str | None = None, timeout: float | None = 600
) -> TestResult:
    result = sandbox.exec(["sh", "-c", command], timeout=timeout)
    if junit_xml:
        return parse_junit(junit_xml)
    # No structured report: infer from exit code.
    if result.exit_code == 0 and not result.timed_out:
        return TestResult(passed=1)
    return TestResult(failed=1, failures=[result.stderr.strip() or f"exit {result.exit_code}"])
