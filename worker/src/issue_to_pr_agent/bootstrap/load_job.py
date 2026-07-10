"""Load the Job the container was handed (env var, or a file path)."""

from __future__ import annotations

import os
from pathlib import Path

from ..errors import BootstrapError
from ..job import Job


def load_job(env: dict[str, str] | None = None) -> Job:
    """Load the Job from ITPR_JOB (JSON) or ITPR_JOB_FILE (path to JSON)."""
    source = env if env is not None else dict(os.environ)
    raw = source.get("ITPR_JOB")
    if raw is None:
        file = source.get("ITPR_JOB_FILE")
        if file:
            try:
                raw = Path(file).read_text(encoding="utf-8")
            except OSError as exc:
                raise BootstrapError(f"cannot read ITPR_JOB_FILE: {exc}") from exc
    if not raw:
        raise BootstrapError("no job provided (set ITPR_JOB or ITPR_JOB_FILE)")
    return Job.from_json(raw)
