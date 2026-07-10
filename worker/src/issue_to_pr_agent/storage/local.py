"""Filesystem-backed artifact store — the fallback when S3 is unavailable.

Also defines the ``Storage`` protocol both backends implement, kept here (a leaf
module) so ``s3``/``run_artifacts``/``trace_archive`` can import it without a
package-import cycle. Keys are ``/``-separated and jailed under the root, so a
key can never escape the artifact directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from ..errors import StorageError


@runtime_checkable
class Storage(Protocol):
    """Common backend surface: opaque keys in, bytes out. Same for S3 + local."""

    scheme: str

    def put(self, key: str, data: bytes) -> str: ...
    def get(self, key: str) -> bytes: ...
    def exists(self, key: str) -> bool: ...
    def list(self, prefix: str = "") -> list[str]: ...


def _normalize(key: str) -> str:
    key = key.strip().lstrip("/")
    if not key or ".." in key.split("/"):
        raise StorageError(f"invalid artifact key: {key!r}")
    return key


class LocalStorage:
    """Stores artifacts as files under ``root``; ``root`` is created on demand."""

    scheme = "file"

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / _normalize(key)).resolve()
        root = self.root.resolve()
        if root != path and root not in path.parents:
            raise StorageError(f"key escapes storage root: {key!r}")
        return path

    def put(self, key: str, data: bytes) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"file://{path}"

    def get(self, key: str) -> bytes:
        path = self._path(key)
        try:
            return path.read_bytes()
        except FileNotFoundError as exc:
            raise StorageError(f"artifact not found: {key!r}") from exc

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def list(self, prefix: str = "") -> list[str]:
        root = self.root.resolve()
        keys = [
            str(p.resolve().relative_to(root)).replace("\\", "/")
            for p in self.root.rglob("*")
            if p.is_file()
        ]
        prefix = prefix.lstrip("/")
        return sorted(k for k in keys if k.startswith(prefix))
