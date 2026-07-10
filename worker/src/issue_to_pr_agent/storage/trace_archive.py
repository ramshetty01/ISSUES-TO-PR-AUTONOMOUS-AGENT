"""Archive of run traces, kept apart from live run artifacts.

Stores the redacted trace bundle produced by observability (phase 29) under a
stable ``traces/{run_id}.tar.gz`` key so traces can be retained/retrieved
independently of the run's working artifacts.
"""

from __future__ import annotations

import json
from typing import Any, cast

from .local import Storage

TRACES_PREFIX = "traces"


class TraceArchive:
    """Persists and retrieves archived traces on any ``Storage`` backend."""

    def __init__(self, storage: Storage) -> None:
        self._storage = storage

    def archive_key(self, run_id: str) -> str:
        return f"{TRACES_PREFIX}/{run_id}.tar.gz"

    def json_key(self, run_id: str) -> str:
        return f"{TRACES_PREFIX}/{run_id}.json"

    def archive(self, run_id: str, data: bytes) -> str:
        """Store a redacted trace archive (tar.gz bytes); return its URI."""
        return self._storage.put(self.archive_key(run_id), data)

    def archive_trace(self, run_id: str, trace: dict[str, Any]) -> str:
        """Store an exported trace payload as JSON; return its URI."""
        return self._storage.put(
            self.json_key(run_id), json.dumps(trace, indent=2).encode("utf-8")
        )

    def fetch(self, run_id: str) -> bytes:
        return self._storage.get(self.archive_key(run_id))

    def fetch_trace(self, run_id: str) -> dict[str, Any]:
        raw = self._storage.get(self.json_key(run_id))
        return cast(dict[str, Any], json.loads(raw.decode("utf-8")))

    def exists(self, run_id: str) -> bool:
        return self._storage.exists(self.archive_key(run_id))
