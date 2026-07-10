"""Create the isolated working directory for a run, confined under a jail root."""

from __future__ import annotations

import shutil
from pathlib import Path

from ..errors import BootstrapError


def prepare_workspace(jail_root: Path, run_id: str) -> Path:
    """Create (or reset) a clean workspace for `run_id` under `jail_root`.

    The returned path is guaranteed to be inside jail_root — a run can never
    escape the jail via a crafted run id.
    """
    jail_root = jail_root.resolve()
    ws = (jail_root / run_id).resolve()
    if jail_root not in ws.parents and ws != jail_root:
        raise BootstrapError("workspace path escapes the jail root")
    if ws == jail_root:
        raise BootstrapError("workspace cannot be the jail root itself")
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True, exist_ok=False)
    return ws
