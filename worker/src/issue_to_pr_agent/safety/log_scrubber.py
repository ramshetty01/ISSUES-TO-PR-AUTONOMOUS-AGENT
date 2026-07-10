"""Redact secrets (and optionally PII) from text before it is logged/stored.

Idempotent: placeholders never re-match a pattern.
"""

from __future__ import annotations

import re
from typing import Any

from .pii_scanner import _PATTERNS as _PII_PATTERNS
from .secret_scanner import _PATTERNS as _SECRET_PATTERNS


def _placeholder(kind: str) -> str:
    return f"[REDACTED:{kind}]"


def scrub(text: str, *, pii: bool = False) -> str:
    out = text
    for kind, rx in _SECRET_PATTERNS:
        out = re.sub(rx, _placeholder(kind), out)
    if pii:
        for kind, rx in _PII_PATTERNS:
            out = re.sub(rx, _placeholder(kind), out)
    return out


def scrub_deep(value: Any, *, pii: bool = False) -> Any:
    if isinstance(value, str):
        return scrub(value, pii=pii)
    if isinstance(value, list):
        return [scrub_deep(v, pii=pii) for v in value]
    if isinstance(value, dict):
        return {k: scrub_deep(v, pii=pii) for k, v in value.items()}
    return value
