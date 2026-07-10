"""Per-run context threaded through the worker pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .config import WorkerConfig
from .job import Job


@dataclass(slots=True)
class RuntimeContext:
    """Everything a single run needs: the job, config, run id, and workspace."""

    job: Job
    config: WorkerConfig
    run_id: str
    workspace: Path
    events: list[str] = field(default_factory=list)

    def log_event(self, message: str) -> None:
        self.events.append(message)
