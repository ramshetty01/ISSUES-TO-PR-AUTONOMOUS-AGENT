"""Workspace + container cleanup helpers (best-effort, never raise)."""

from __future__ import annotations

import shutil
from pathlib import Path


def cleanup_workspace(workspace: Path) -> None:
    try:
        if workspace.exists():
            shutil.rmtree(workspace)
    except OSError:
        pass
