"""Scan for PII (emails, IPv4, phone numbers)."""

from __future__ import annotations

import re
from dataclasses import dataclass

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    ("ipv4", re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
    )),
    ("phone", re.compile(r"(?<!\d)(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)")),
]


@dataclass(slots=True)
class PiiFinding:
    kind: str
    match: str


def scan_pii(text: str) -> list[PiiFinding]:
    findings: list[PiiFinding] = []
    for kind, rx in _PATTERNS:
        for m in rx.finditer(text):
            findings.append(PiiFinding(kind, m.group(0)))
    return findings
