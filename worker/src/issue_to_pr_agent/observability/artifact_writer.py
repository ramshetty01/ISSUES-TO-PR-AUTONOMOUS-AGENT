"""Persist run artifacts to disk with log-redaction applied.

Every value written passes through the safety scrubber first, so nothing
containing a secret (and optionally PII) is ever persisted. Files land under a
per-run directory; ``storage/`` (phase 30) uploads that directory afterwards.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..safety.log_scrubber import scrub, scrub_deep


class ArtifactWriter:
    """Writes redacted JSON/text artifacts into a per-run directory."""

    def __init__(self, root: Path | str, *, pii: bool = False) -> None:
        self.root = Path(root)
        self._pii = pii
        self.root.mkdir(parents=True, exist_ok=True)
        self._written: list[Path] = []

    def write_json(self, name: str, obj: Any) -> Path:
        redacted = scrub_deep(obj, pii=self._pii)
        path = self.root / name
        path.write_text(json.dumps(redacted, indent=2, sort_keys=False) + "\n", encoding="utf-8")
        self._written.append(path)
        return path

    def write_text(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_text(scrub(text, pii=self._pii), encoding="utf-8")
        self._written.append(path)
        return path

    @property
    def paths(self) -> list[Path]:
        return list(self._written)
