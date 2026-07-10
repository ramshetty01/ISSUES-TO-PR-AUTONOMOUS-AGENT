"""Normalized test-suite result."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class TestResult:
    __test__ = False  # not a pytest test class

    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    failures: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.errors + self.skipped

    @property
    def ok(self) -> bool:
        return self.failed == 0 and self.errors == 0
