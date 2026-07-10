"""Worker entrypoint: load job + config, build the run context, run the pipeline.

The pipeline stages (bootstrap, sandbox, inference, agent, verification, safety,
PR authoring) are wired in later phases; for now main assembles the context and
returns a clean exit code so the container is runnable end-to-end.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

from .config import WorkerConfig
from .errors import WorkerError
from .job import Job
from .runtime_context import RuntimeContext


def build_context() -> RuntimeContext:
    """Assemble the RuntimeContext from the process environment."""
    config = WorkerConfig()
    raw_job = os.environ.get("ITPR_JOB")
    if not raw_job:
        raise WorkerError("ITPR_JOB is not set")
    job = Job.from_json(raw_job)
    run_id = os.environ.get("ITPR_JOB_ID") or job.id or uuid.uuid4().hex
    workspace = Path(os.environ.get("ITPR_WORKSPACE", "/workspace"))
    return RuntimeContext(job=job, config=config, run_id=run_id, workspace=workspace)


def run(ctx: RuntimeContext) -> int:
    """Run the pipeline. Stub for now — later phases fill the stages."""
    ctx.log_event(f"run {ctx.run_id} started for {ctx.job.repo.owner}/{ctx.job.repo.name}")
    ctx.log_event("pipeline stub — stages wired in later phases")
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        ctx = build_context()
    except WorkerError as exc:
        print(f"worker bootstrap error: {exc}", file=sys.stderr)
        return 2
    return run(ctx)


if __name__ == "__main__":
    raise SystemExit(main())
