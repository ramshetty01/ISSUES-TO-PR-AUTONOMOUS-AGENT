"""Structured per-run artifact layout on top of any ``Storage`` backend.

Stable layout (same on S3 and local), consumed by observability (phase 29)::

    runs/{run_id}/summary.json      run summary (shared-types RunSummary)
    runs/{run_id}/trace.json        exported trace payload
    runs/{run_id}/events.json       timeline events
    runs/{run_id}/cost.json         cost report
    runs/{run_id}/archive.tar.gz    redacted artifact archive

``RunArtifacts`` owns the key prefix so callers write by short name and never
hand-build keys.
"""

from __future__ import annotations

import json
from typing import Any

from .local import Storage

RUNS_PREFIX = "runs"

# Canonical artifact names (the stable, documented layout).
SUMMARY = "summary.json"
TRACE = "trace.json"
EVENTS = "events.json"
COST = "cost.json"
ARCHIVE = "archive.tar.gz"


class RunArtifacts:
    """Reads/writes the artifacts for a single run under ``runs/{run_id}/``."""

    def __init__(self, storage: Storage, run_id: str) -> None:
        if not run_id:
            raise ValueError("run_id is required")
        self._storage = storage
        self.run_id = run_id

    def key(self, name: str) -> str:
        return f"{RUNS_PREFIX}/{self.run_id}/{name}"

    def put_bytes(self, name: str, data: bytes) -> str:
        return self._storage.put(self.key(name), data)

    def put_text(self, name: str, text: str) -> str:
        return self._storage.put(self.key(name), text.encode("utf-8"))

    def put_json(self, name: str, obj: Any) -> str:
        return self.put_text(name, json.dumps(obj, indent=2))

    def get_bytes(self, name: str) -> bytes:
        return self._storage.get(self.key(name))

    def get_json(self, name: str) -> Any:
        return json.loads(self.get_bytes(name).decode("utf-8"))

    def exists(self, name: str) -> bool:
        return self._storage.exists(self.key(name))

    def list(self) -> list[str]:
        """Artifact names present for this run (prefix stripped)."""
        prefix = f"{RUNS_PREFIX}/{self.run_id}/"
        return [k[len(prefix) :] for k in self._storage.list(prefix)]
