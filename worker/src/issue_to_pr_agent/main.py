"""Worker entrypoint: run the bootstrap sequence, then the end-to-end pipeline.

Bootstrap (tools check, job load+validate, jailed workspace, time budget) is
wired here; the full run pipeline (context -> agent -> safety -> verification ->
PR authoring -> observability/storage) lives in :mod:`pipeline` and is invoked
from :func:`run`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .bootstrap import DEFAULT_TIME_BUDGET_SECONDS, bootstrap
from .bootstrap.time_budget import TimeBudget
from .config import WorkerConfig
from .errors import WorkerError
from .llm import build_client
from .pipeline import run_pipeline
from .runtime_context import RuntimeContext
from .sandbox.manager import create_sandbox
from .storage import open_storage


def run(ctx: RuntimeContext, budget: TimeBudget) -> int:
    """Assemble the run's collaborators and drive the pipeline."""
    ctx.log_event(f"run {ctx.run_id} started for {ctx.job.repo.owner}/{ctx.job.repo.name}")
    ctx.log_event(f"workspace={ctx.workspace} budget_remaining={budget.remaining():.0f}s")

    llm = build_client(ctx.config)
    sandbox_image = os.environ.get("ITPR_SANDBOX_IMAGE", "itpr-worker:local")
    sandbox = create_sandbox(sandbox_image, ctx.workspace)

    github = None
    if ctx.config.github_installation_token:
        from .github.client import GitHubClient

        github = GitHubClient(ctx.config.github_installation_token)

    storage = None
    try:
        storage = open_storage(ctx.config)
    except Exception as exc:  # storage is optional; keep running
        ctx.log_event(f"storage unavailable: {exc}")

    try:
        result = run_pipeline(ctx, sandbox=sandbox, llm=llm, github=github, storage=storage)
    except WorkerError as exc:
        ctx.log_event(f"pipeline error: {exc}")
        return 2

    ctx.log_event(f"run {ctx.run_id} finished: {result.summary.state}")
    return result.exit_code


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
