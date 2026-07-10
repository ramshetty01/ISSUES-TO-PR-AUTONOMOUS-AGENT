"""Worker entrypoint: run the bootstrap sequence, then the pipeline.

The bootstrap sequence (tools check, job load+validate, jailed workspace, time
budget) is wired here; later phases fill the remaining pipeline stages (sandbox,
inference, agent, verification, safety, PR authoring).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .bootstrap import DEFAULT_TIME_BUDGET_SECONDS, bootstrap
from .bootstrap.time_budget import TimeBudget
from .config import WorkerConfig
from .errors import WorkerError
from .runtime_context import RuntimeContext


def run(ctx: RuntimeContext, budget: TimeBudget) -> int:
    """Run the pipeline. Stub for now — later phases fill the stages."""
    ctx.log_event(
        f"run {ctx.run_id} started for {ctx.job.repo.owner}/{ctx.job.repo.name}"
    )
    ctx.log_event(f"workspace={ctx.workspace} budget_remaining={budget.remaining():.0f}s")
    ctx.log_event("pipeline stub — stages wired in later phases")
    return 0


def main(argv: list[str] | None = None) -> int:
    config = WorkerConfig()
    jail_root = Path(os.environ.get("ITPR_WORKSPACE_ROOT", "/workspace"))
    try:
        ctx, budget = bootstrap(
            config,
            jail_root=jail_root,
            time_budget_seconds=DEFAULT_TIME_BUDGET_SECONDS,
        )
    except WorkerError as exc:
        print(f"worker bootstrap error: {exc}", file=sys.stderr)
        return 2
    return run(ctx, budget)


if __name__ == "__main__":
    raise SystemExit(main())
