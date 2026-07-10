"""Phase 17 skeleton tests: Job model, config, and the entry pipeline."""

from __future__ import annotations

import json

import pytest

from issue_to_pr_agent import Job, WorkerConfig
from issue_to_pr_agent.errors import BootstrapError, SafetyRefusal

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


def test_main_runs_full_bootstrap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    from pathlib import Path

    import issue_to_pr_agent.main as main_mod

    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setenv("ITPR_JOB", json.dumps(CAMEL_JOB))
    monkeypatch.setenv("ITPR_JOB_ID", "d-1")
    monkeypatch.setenv("GITHUB_INSTALLATION_TOKEN", "ghs_x")
    monkeypatch.setenv("ITPR_WORKSPACE_ROOT", str(Path(str(tmp_path))))
    assert main_mod.main() == 0


def test_main_returns_2_without_job(monkeypatch: pytest.MonkeyPatch) -> None:
    import issue_to_pr_agent.main as main_mod

    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}")
    monkeypatch.delenv("ITPR_JOB", raising=False)
    monkeypatch.delenv("ITPR_JOB_FILE", raising=False)
    assert main_mod.main() == 2


def test_safety_refusal_carries_reason() -> None:
    err = SafetyRefusal("secret_detected", "token found")
    assert err.reason == "secret_detected"
    assert "token found" in str(err)
