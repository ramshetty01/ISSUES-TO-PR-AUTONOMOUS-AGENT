"""Guard against committing credentials: scan a proposed diff before commit."""

from __future__ import annotations

from .refusal import refuse
from .secret_scanner import scan_secrets


def assert_diff_has_no_secrets(diff: str) -> None:
    """Refuse a commit whose added lines introduce a secret."""
    added = "\n".join(
        line[1:] for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    findings = scan_secrets(added)
    if findings:
        kinds = ", ".join(sorted({f.kind for f in findings}))
        raise refuse("secret_detected", "commit would introduce a secret", kinds)
