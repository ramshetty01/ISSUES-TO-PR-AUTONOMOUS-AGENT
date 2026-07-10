"""End-to-end integration test for the run pipeline.

Proves the worker's subsystems are actually wired together: with a mock LLM, a
local (non-Docker) sandbox, a real git workspace, and no GitHub, the pipeline
runs context -> agent -> safety -> verification -> observability/storage and
produces a valid RunSummary plus persisted artifacts. No network, no Docker.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from issue_to_pr_agent.agent import action_json
from issue_to_pr_agent.config import WorkerConfig
from issue_to_pr_agent.job import Job
from issue_to_pr_agent.llm.client import LLMClient
from issue_to_pr_agent.llm.providers.mock import MockProvider
from issue_to_pr_agent.llm.router import Router
from issue_to_pr_agent.pipeline import run_pipeline
from issue_to_pr_agent.runtime_context import RuntimeContext
from issue_to_pr_agent.sandbox.base import Sandbox
from issue_to_pr_agent.sandbox.command_runner import CommandResult
from issue_to_pr_agent.storage import LocalStorage


class LocalSandbox(Sandbox):
    """Runs commands on the host inside the workspace (test-only, no isolation)."""

    def __init__(self, workspace: Path) -> None:
        self._ws = workspace

    @property
    def workspace(self) -> Path:
        return self._ws

    def start(self) -> None:
        pass

    def exec(self, argv: list[str], *, timeout: float | None = None) -> CommandResult:
        proc = subprocess.run(argv, cwd=self._ws, capture_output=True, text=True, timeout=timeout)
        return CommandResult(
            exit_code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr, timed_out=False
        )

    def read_file(self, relpath: str) -> str:
        return (self._ws / relpath).read_text()

    def write_file(self, relpath: str, content: str) -> None:
        (self._ws / relpath).write_text(content)

    def teardown(self) -> None:
        pass


def _git(ws: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=ws, check=True, capture_output=True)


def _repo(tmp_path: Path) -> Path:
    ws = tmp_path / "repo"
    ws.mkdir()
    (ws / "app.py").write_text("def handle(x):\n    return x\n")
    _git(ws, "init", "-q")
    _git(ws, "config", "user.email", "t@t.t")
    _git(ws, "config", "user.name", "t")
    _git(ws, "add", "-A")
    _git(ws, "commit", "-qm", "init")
    return ws


def _mock_llm() -> LLMClient:
    # The mock immediately returns a successful finish action, so the agent loop
    # terminates on turn one.
    provider = MockProvider(response=action_json(finish=True, success=True))
    return LLMClient(Router([provider]))


def _ctx(ws: Path) -> RuntimeContext:
    job = Job.model_validate(
        {
            "id": "run-int-1",
            "repo": {"owner": "acme", "name": "widgets"},
            "installationId": 1,
            "trigger": "issue_labeled",
            "issueNumber": 7,
        }
    )
    return RuntimeContext(job=job, config=WorkerConfig(), run_id="run-int-1", workspace=ws)


def test_pipeline_runs_end_to_end(tmp_path: Path) -> None:
    ws = _repo(tmp_path)
    storage = LocalStorage(tmp_path / "store")
    result = run_pipeline(
        _ctx(ws),
        sandbox=LocalSandbox(ws),
        llm=_mock_llm(),
        github=None,          # no GitHub -> PR authoring is skipped, not failed
        storage=storage,
        test_command="true",  # trivially-passing test command
    )

    # The run completed with a valid, shared-types-shaped summary.
    assert result.exit_code == 0
    summary = result.summary.to_dict()
    assert summary["runId"] == "run-int-1"
    assert summary["state"] == "succeeded"
    assert summary["job"]["installationId"] == 1
    assert summary["traceUrl"].endswith("/trace/run-int-1")

    # Every stage recorded a timeline event -> the subsystems actually ran.
    kinds = {e["kind"] for e in summary["timeline"]}
    assert {"start", "agent", "safety", "verify", "test"} <= kinds

    # Observability artifacts were persisted to object storage.
    ra_keys = storage.list("runs/run-int-1/")
    assert "runs/run-int-1/summary.json" in ra_keys
    assert storage.exists("traces/run-int-1.json")

    # Local redacted artifacts were written too.
    assert (ws / ".itpr" / "run-int-1" / "summary.json").is_file()
    assert (ws / ".itpr" / "run-int-1.tar.gz").is_file()


def test_pipeline_refuses_diff_with_secret(tmp_path: Path) -> None:
    ws = _repo(tmp_path)
    # Stage an uncommitted change containing a secret; finalize's `git diff` will
    # surface it, and the safety gate must refuse the run.
    token = "".join(["ghp", "_", "0123456789abcdefghijklmnopqrstuvwxyz"])
    (ws / "app.py").write_text(f"TOKEN = '{token}'\n")

    result = run_pipeline(
        _ctx(ws),
        sandbox=LocalSandbox(ws),
        llm=_mock_llm(),
        github=None,
        test_command="true",
    )
    summary = result.summary.to_dict()
    assert summary["state"] == "refused"
    assert summary["refusal"]["reason"] == "secret_detected"
    assert result.exit_code == 0  # a refusal is a valid terminal outcome
    assert token not in summary["refusal"]["message"]  # the refusal itself is scrubbed-safe
