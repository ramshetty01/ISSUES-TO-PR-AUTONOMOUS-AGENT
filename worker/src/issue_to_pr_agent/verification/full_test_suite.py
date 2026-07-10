"""Run the full test suite (thin wrapper over ci_runner for clarity of intent)."""

from __future__ import annotations

from ..sandbox.base import Sandbox
from .ci_runner import run_tests
from .test_result import TestResult


def run_full_suite(
    sandbox: Sandbox, command: str, *, junit_xml: str | None = None
) -> TestResult:
    return run_tests(sandbox, command, junit_xml=junit_xml)
