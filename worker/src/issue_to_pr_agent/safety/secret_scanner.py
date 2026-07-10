"""Scan text/diffs for secrets. Python port of the log-redaction patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .refusal import refuse

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private_key", re.compile(
        r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z]+ )?PRIVATE KEY-----"
    )),
    ("github_token", re.compile(r"\bgh[opusr]_[A-Za-z0-9]{36}\b")),
    ("github_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{60,}\b")),
    ("aws_access_key_id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/\-]{10,}=*")),
    ("generic_secret", re.compile(
        r"\b(?:api[_-]?key|secret|token|password|passwd|access[_-]?key)\b\s*[:=]\s*['\"]?[A-Za-z0-9._\-]{12,}",
        re.IGNORECASE,
    )),
]


@dataclass(slots=True)
class SecretFinding:
    kind: str
    match: str


def scan_secrets(text: str) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for kind, rx in _PATTERNS:
        for m in rx.finditer(text):
            findings.append(SecretFinding(kind, m.group(0)))
    return findings


def has_secret(text: str) -> bool:
    return any(rx.search(text) for _, rx in _PATTERNS)


def assert_no_secrets(text: str, *, where: str = "content") -> None:
    findings = scan_secrets(text)
    if findings:
        kinds = ", ".join(sorted({f.kind for f in findings}))
        raise refuse("secret_detected", f"secret(s) detected in {where}", kinds)
