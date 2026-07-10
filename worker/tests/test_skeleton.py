"""Phase 17 skeleton tests: Job model, config, and the entry pipeline."""

from __future__ import annotations

import json

import pytest

from issue_to_pr_agent import Job, WorkerConfig
from issue_to_pr_agent.errors import BootstrapError, SafetyRefusal
from issue_to_pr_agent.main import build_context, run

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


def test_job_parses_camelcase_from_wire() -> None:
    job = Job.from_json(json.dumps(CAMEL_JOB))
    assert job.id == "d-1"
    assert job.repo.owner == "acme"
    assert job.installation_id == 42
    assert job.trigger == "issue_labeled"
    assert job.issue_number == 7
    assert job.pr_number is None


def test_job_rejects_malformed() -> None:
    with pytest.raises(BootstrapError):
        Job.from_json("not-json")
    with pytest.raises(BootstrapError):
        Job.from_json(json.dumps({"id": "x"}))  # missing repo/installationId


def test_config_provider_order_splits() -> None:
    cfg = WorkerConfig(LLM_PROVIDER_ORDER="nvidia_nim, groq ,mock")  # type: ignore[call-arg]
    assert cfg.provider_order == ["nvidia_nim", "groq", "mock"]


def test_build_context_and_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ITPR_JOB", json.dumps(CAMEL_JOB))
    monkeypatch.setenv("ITPR_JOB_ID", "d-1")
    ctx = build_context()
    assert ctx.run_id == "d-1"
    assert ctx.job.repo.name == "widgets"
    assert run(ctx) == 0
    assert any("started" in e for e in ctx.events)


def test_build_context_requires_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ITPR_JOB", raising=False)
    from issue_to_pr_agent.errors import WorkerError

    with pytest.raises(WorkerError):
        build_context()


def test_safety_refusal_carries_reason() -> None:
    err = SafetyRefusal("secret_detected", "token found")
    assert err.reason == "secret_detected"
    assert "token found" in str(err)
