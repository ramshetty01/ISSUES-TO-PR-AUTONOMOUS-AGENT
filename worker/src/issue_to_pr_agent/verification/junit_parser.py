"""Parse JUnit XML into a TestResult."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from .test_result import TestResult


def parse_junit(xml: str) -> TestResult:
    root = ET.fromstring(xml)
    suites = [root] if root.tag == "testsuite" else root.findall(".//testsuite")
    result = TestResult()
    for suite in suites:
        tests = int(suite.get("tests", 0))
        failed = int(suite.get("failures", 0))
        errors = int(suite.get("errors", 0))
        skipped = int(suite.get("skipped", 0))
        result.failed += failed
        result.errors += errors
        result.skipped += skipped
        result.passed += max(0, tests - failed - errors - skipped)
        for case in suite.findall("testcase"):
            for tag in ("failure", "error"):
                node = case.find(tag)
                if node is not None:
                    name = case.get("name", "?")
                    result.failures.append(f"{name}: {node.get('message', tag)}")
    return result
