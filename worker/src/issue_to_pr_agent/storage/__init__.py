"""Artifact persistence: S3 (LocalStack or real AWS) with a local fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import WorkerConfig
from .local import LocalStorage, Storage
from .run_artifacts import RunArtifacts
from .s3 import S3Storage
from .trace_archive import TraceArchive

DEFAULT_LOCAL_ROOT = Path(".itpr-artifacts")


def open_storage(
    config: WorkerConfig,
    *,
    prefer_s3: bool = True,
    s3_client: Any | None = None,
    local_root: Path | str | None = None,
) -> Storage:
    """Return an S3 store when reachable, else the filesystem fallback.

    The same call works against LocalStack and real AWS. If S3 can't be reached
    (boto3 missing, endpoint down, bucket unreachable) it degrades to
    ``LocalStorage`` so a run never fails purely because object storage is off.
    """
    if prefer_s3:
        try:
            store = S3Storage.from_config(config, client=s3_client)
            store.ensure_bucket()
            if store.available():
                return store
        except Exception:  # any wiring/network failure -> local fallback
            pass
    return LocalStorage(local_root or DEFAULT_LOCAL_ROOT)


__all__ = [
    "Storage",
    "LocalStorage",
    "S3Storage",
    "RunArtifacts",
    "TraceArchive",
    "open_storage",
    "DEFAULT_LOCAL_ROOT",
]
