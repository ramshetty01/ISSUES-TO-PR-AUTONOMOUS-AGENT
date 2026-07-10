"""Terminal run summary — the worker's outcome record.

Matches ``RunSummary`` in packages/shared-types/src/run.ts (camelCase on the
wire) and feeds both the dashboard and examples/run-summary.example.json.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..job import Job

# Kept in sync with RunState in shared-types run.ts.
RUN_STATES = frozenset(
    {"queued", "dispatched", "running", "succeeded", "failed", "refused"}
)


@dataclass(slots=True)
class RunSummary:
    """Outcome summary emitted at the end of a run."""

    run_id: str
    job: Job
    state: str
    started_at: str
    timeline: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=lambda: {"input": 0, "output": 0, "total": 0})
    dollars: float = 0.0
    safety_events: list[dict[str, Any]] = field(default_factory=list)
    refusal: dict[str, Any] | None = None
    pr_url: str | None = None
    trace_url: str | None = None
    finished_at: str | None = None

    def __post_init__(self) -> None:
        if self.state not in RUN_STATES:
            raise ValueError(f"unknown run state: {self.state!r}")

    def to_dict(self) -> dict[str, Any]:
        """Serialise to the shared-types RunSummary shape (camelCase)."""
        out: dict[str, Any] = {
            "runId": self.run_id,
            "job": self.job.model_dump(by_alias=True),
            "state": self.state,
            "timeline": self.timeline,
            "usage": self.usage,
            "dollars": round(self.dollars, 6),
            "safetyEvents": self.safety_events,
            "startedAt": self.started_at,
        }
        if self.refusal is not None:
            out["refusal"] = self.refusal
        if self.pr_url is not None:
            out["prUrl"] = self.pr_url
        if self.trace_url is not None:
            out["traceUrl"] = self.trace_url
        if self.finished_at is not None:
            out["finishedAt"] = self.finished_at
        return out


def build_run_summary(
    *,
    run_id: str,
    job: Job,
    state: str,
    started_at: str,
    timeline: list[dict[str, Any]] | None = None,
    usage: dict[str, int] | None = None,
    dollars: float = 0.0,
    safety_events: list[dict[str, Any]] | None = None,
    refusal: dict[str, Any] | None = None,
    pr_url: str | None = None,
    trace_url: str | None = None,
    finished_at: str | None = None,
) -> RunSummary:
    """Assemble a validated ``RunSummary`` from run outputs."""
    return RunSummary(
        run_id=run_id,
        job=job,
        state=state,
        started_at=started_at,
        timeline=timeline or [],
        usage=usage or {"input": 0, "output": 0, "total": 0},
        dollars=dollars,
        safety_events=safety_events or [],
        refusal=refusal,
        pr_url=pr_url,
        trace_url=trace_url,
        finished_at=finished_at,
    )
