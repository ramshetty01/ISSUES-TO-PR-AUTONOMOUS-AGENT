"""Bundle run artifacts into a single redacted ``.tar.gz`` safe to store.

Each member is scrubbed before it enters the archive, and ``verify_no_secrets``
re-scans the written archive as a defence-in-depth check so a leaking pattern
fails loudly instead of being persisted.
"""

from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path
from typing import Any

from ..safety.log_scrubber import scrub, scrub_deep
from ..safety.secret_scanner import has_secret


def _render(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, indent=2, sort_keys=False)


def build_redacted_archive(
    dest: Path | str, artifacts: dict[str, Any], *, pii: bool = False
) -> Path:
    """Write ``artifacts`` (name -> str|JSON-able) into a redacted tar.gz."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(dest, "w:gz") as tar:
        for name, value in artifacts.items():
            redacted = scrub(value, pii=pii) if isinstance(value, str) else scrub_deep(value, pii=pii)
            payload = _render(redacted).encode("utf-8")
            info = tarfile.TarInfo(name=name)
            info.size = len(payload)
            info.mtime = 0  # deterministic archives
            tar.addfile(info, io.BytesIO(payload))
    return dest


def read_members(path: Path | str) -> dict[str, str]:
    """Extract archive members as text (used for verification and tests)."""
    out: dict[str, str] = {}
    with tarfile.open(path, "r:gz") as tar:
        for member in tar.getmembers():
            fh = tar.extractfile(member)
            out[member.name] = fh.read().decode("utf-8") if fh else ""
    return out


def verify_no_secrets(path: Path | str) -> bool:
    """True when no archived member still trips the secret scanner."""
    return not any(has_secret(text) for text in read_members(path).values())
