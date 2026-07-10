"""Path-jailed filesystem access: every read/write is confined to the workspace."""

from __future__ import annotations

from pathlib import Path

from ..errors import SafetyRefusal


class PathJail:
    """Confines all file access to a root directory. Escapes raise SafetyRefusal."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def resolve(self, relpath: str | Path) -> Path:
        """Resolve `relpath` under the jail; raise if it escapes."""
        candidate = (self.root / relpath).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise SafetyRefusal("path_jail_escape", f"path escapes workspace: {relpath}")
        return candidate

    def read_text(self, relpath: str | Path) -> str:
        return self.resolve(relpath).read_text(encoding="utf-8")

    def write_text(self, relpath: str | Path, content: str) -> Path:
        p = self.resolve(relpath)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def exists(self, relpath: str | Path) -> bool:
        try:
            return self.resolve(relpath).exists()
        except SafetyRefusal:
            return False
