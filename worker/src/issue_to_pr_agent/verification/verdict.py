"""The aggregate verification verdict."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Verdict:
    passed: bool
    checks: dict[str, bool] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)

    def record(self, name: str, ok: bool, reason: str = "") -> None:
        self.checks[name] = ok
        if not ok and reason:
            self.reasons.append(reason)
