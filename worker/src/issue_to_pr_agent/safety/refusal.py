"""Structured safety refusals."""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import SafetyRefusal

# Refusal reason codes (kept in sync with shared-types safety.ts).
REASONS = {
    "forbidden_path",
    "workflow_write_blocked",
    "force_push_blocked",
    "secret_detected",
    "pii_detected",
    "command_denied",
    "path_jail_escape",
    "diff_too_large",
}


@dataclass(slots=True)
class Refusal:
    reason: str
    message: str
    detail: str | None = None


def refuse(reason: str, message: str, detail: str | None = None) -> SafetyRefusal:
    """Build (not raise) a SafetyRefusal carrying the reason."""
    full = message if not detail else f"{message}: {detail}"
    return SafetyRefusal(reason, full)
