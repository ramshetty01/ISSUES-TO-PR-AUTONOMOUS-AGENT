"""Extract structured output (code blocks, JSON) from a model response."""

from __future__ import annotations

import json
import re
from typing import Any

_CODE_BLOCK = re.compile(r"```(?:[\w+-]*)\n(.*?)```", re.DOTALL)


def extract_code_blocks(text: str) -> list[str]:
    return [m.group(1).rstrip("\n") for m in _CODE_BLOCK.finditer(text)]


def extract_json(text: str) -> Any | None:
    """Parse the first JSON object/array — from a fenced block or raw braces."""
    for block in extract_code_blocks(text):
        try:
            return json.loads(block)
        except json.JSONDecodeError:
            continue
    # Fall back to the first {...} or [...] span.
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
    return None
