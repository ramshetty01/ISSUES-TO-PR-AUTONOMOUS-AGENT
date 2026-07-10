"""Block dangerous shell commands before they run in the sandbox."""

from __future__ import annotations

import re
from pathlib import Path

from .refusal import refuse

# Patterns matched against the full command string (case-insensitive).
DEFAULT_DENYLIST = [
    r"\brm\s+-rf\s+/(?:\s|$)",          # rm -rf /
    r":\(\)\s*\{.*\|.*&\s*\}\s*;",       # fork bomb
    r"\bmkfs\b",                          # format filesystem
    r"\bdd\s+if=.*of=/dev/",              # overwrite a device
    r"curl\s+[^|]*\|\s*(?:ba)?sh",        # curl | sh
    r"wget\s+[^|]*\|\s*(?:ba)?sh",        # wget | sh
    r">\s*/dev/sd[a-z]",                  # write to a raw disk
    r"\bchmod\s+-R\s+777\s+/",            # world-writable root
]


def find_denied(command: str, denylist: list[str] = DEFAULT_DENYLIST) -> str | None:
    for pattern in denylist:
        if re.search(pattern, command, re.IGNORECASE):
            return pattern
    return None


def assert_command_allowed(command: str, denylist: list[str] = DEFAULT_DENYLIST) -> None:
    hit = find_denied(command, denylist)
    if hit is not None:
        raise refuse("command_denied", "command blocked by denylist", command.strip())


def load_denylist(path: str | Path) -> list[str]:
    import yaml

    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return doc.get("deny", DEFAULT_DENYLIST)
