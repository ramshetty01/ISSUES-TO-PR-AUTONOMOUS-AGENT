"""Phase 18 bootstrap tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from issue_to_pr_agent.bootstrap import (
    TimeBudget,
    bootstrap,
    ensure_tools,
    load_job,
    prepare_workspace,
    validate_job,
)
from issue_to_pr_agent.config import WorkerConfig
from issue_to_pr_agent.errors import BootstrapError
from issue_to_pr_agent.job import Job

CAMEL_JOB = {
    "id": "d-1",
    "repo": {"owner": "acme", "name": "widgets"},
    "installationId": 42,
    "trigger": "issue_labeled",
    "issueNumber": 7,
    "headSha": "",
    "labels": ["agent-fix"],
    "createdAt": "2026-07-10T12:00:00.000Z",
}


def _job(**over: object) -> Job:
    data = {**CAMEL_JOB, **over}
    return Job.model_validate(data)


def test_load_job_from_env() -> None:
    job = load_job({"ITPR_JOB": json.dumps(CAMEL_JOB)})
    assert job.id == "d-1"


def test_load_job_from_file(tmp_path: Path) -> None:
    f = tmp_path / "job.json"
    f.write_text(json.dumps(CAMEL_JOB), encoding="utf-8")
    job = load_job({"ITPR_JOB_FILE": str(f)})
    assert job.repo.owner == "acme"


def test_load_job_missing() -> None:
    with pytest.raises(BootstrapError):
        load_job({})


def test_validate_job_ok() -> None:
    validate_job(_job(), installation_token="ghs_x")


def test_validate_job_missing_token() -> None:
    with pytest.raises(BootstrapError):
        validate_job(_job(), installation_token="")


def test_validate_job_pr_needs_number() -> None:
    with pytest.raises(BootstrapError):
        validate_job(
            _job(trigger="pr_comment", issueNumber=None, prNumber=None),
            installation_token="ghs_x",
        )


def test_prepare_workspace_confined(tmp_path: Path) -> None:
    ws = prepare_workspace(tmp_path, "run-1")
    assert ws.exists()
    assert tmp_path.resolve() in ws.parents


def test_prepare_workspace_rejects_escape(tmp_path: Path) -> None:
    with pytest.raises(BootstrapError):
        prepare_workspace(tmp_path, "../evil")


def test_prepare_workspace_resets_existing(tmp_path: Path) -> None:
    ws = prepare_workspace(tmp_path, "run-1")
    (ws / "stale.txt").write_text("old", encoding="utf-8")
    ws2 = prepare_workspace(tmp_path, "run-1")
    assert not (ws2 / "stale.txt").exists()


def test_ensure_tools_reports_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _name: None)
    with pytest.raises(BootstrapError):
        ensure_tools(["definitely-not-a-tool"])


def test_time_budget_expiry() -> None:
    t = 0.0

    def clock() -> float:
        return t

    budget = TimeBudget(10, clock=clock)
    assert not budget.expired()
    assert budget.remaining() == 10
    t = 11.0
    assert budget.expired()
    assert budget.fraction_used() == 1.0


def test_bootstrap_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # git/rg live in the container image, not necessarily on the dev host.
    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}")
    cfg = WorkerConfig(
        GITHUB_INSTALLATION_TOKEN="ghs_x",  # type: ignore[call-arg]
        ITPR_JOB_ID="d-1",  # type: ignore[call-arg]
    )
    ctx, budget = bootstrap(
        cfg,
        jail_root=tmp_path,
        time_budget_seconds=60,
        env={"ITPR_JOB": json.dumps(CAMEL_JOB)},
    )
    assert ctx.run_id == "d-1"
    assert ctx.workspace.exists()
    assert budget.remaining() > 0
