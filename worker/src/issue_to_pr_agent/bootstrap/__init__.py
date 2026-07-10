"""Worker startup sequence: load + validate the job, prepare the workspace,
ensure tools, and set the time budget."""

from __future__ import annotations

from pathlib import Path

from ..config import WorkerConfig
from ..runtime_context import RuntimeContext
from .install_tools import ensure_tools
from .load_job import load_job
from .time_budget import TimeBudget
from .validate_job import validate_job
from .workspace import prepare_workspace

DEFAULT_TIME_BUDGET_SECONDS = 15 * 60


def bootstrap(
    config: WorkerConfig,
    *,
    jail_root: Path,
    time_budget_seconds: float = DEFAULT_TIME_BUDGET_SECONDS,
    env: dict[str, str] | None = None,
) -> tuple[RuntimeContext, TimeBudget]:
    """Run the full startup sequence and return the run context + time budget."""
    ensure_tools()
    job = load_job(env)
    validate_job(job, installation_token=config.github_installation_token)
    run_id = config.job_id or job.id
    workspace = prepare_workspace(jail_root, run_id)
    ctx = RuntimeContext(job=job, config=config, run_id=run_id, workspace=workspace)
    return ctx, TimeBudget(time_budget_seconds)


__all__ = [
    "bootstrap",
    "load_job",
    "validate_job",
    "prepare_workspace",
    "ensure_tools",
    "TimeBudget",
    "DEFAULT_TIME_BUDGET_SECONDS",
]
