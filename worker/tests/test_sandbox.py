"""Phase 20 sandbox tests — no real docker needed (injected executor)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from issue_to_pr_agent.errors import SafetyRefusal, SandboxError
from issue_to_pr_agent.sandbox.command_runner import CommandResult, run_command
from issue_to_pr_agent.sandbox.filesystem import PathJail
from issue_to_pr_agent.sandbox.limits import SandboxLimits
from issue_to_pr_agent.sandbox.network_policy import (
    NetworkPolicy,
    blocks_egress,
    to_network_args,
)
from issue_to_pr_agent.sandbox.local_docker import LocalDockerSandbox
from issue_to_pr_agent.sandbox.lifecycle import sandbox_session


def test_network_none_blocks_egress() -> None:
    assert to_network_args(NetworkPolicy.NONE) == ["--network", "none"]
    assert blocks_egress(NetworkPolicy.NONE) is True
    assert blocks_egress(NetworkPolicy.BRIDGE) is False


def test_limits_emit_isolation_flags() -> None:
    s = " ".join(SandboxLimits().to_docker_args())
    assert "--memory 2g" in s
    assert "--pids-limit 512" in s
    assert "--network none" in s
    assert "--read-only" in s
    assert "--cap-drop ALL" in s
    assert "--security-opt no-new-privileges" in s


def test_path_jail_confines(tmp_path: Path) -> None:
    jail = PathJail(tmp_path)
    jail.write_text("sub/file.txt", "hi")
    assert jail.read_text("sub/file.txt") == "hi"
    assert jail.exists("sub/file.txt")


def test_path_jail_rejects_escape(tmp_path: Path) -> None:
    jail = PathJail(tmp_path)
    with pytest.raises(SafetyRefusal):
        jail.resolve("../../etc/passwd")
    with pytest.raises(SafetyRefusal):
        jail.write_text("../escape.txt", "x")
    assert jail.exists("../escape.txt") is False


def test_run_command_captures_output() -> None:
    res = run_command([sys.executable, "-c", "print('hello')"])
    assert res.exit_code == 0
    assert "hello" in res.stdout
    assert res.timed_out is False


def test_run_command_timeout() -> None:
    res = run_command([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.2)
    assert res.timed_out is True
    assert res.exit_code == 124


class FakeDocker:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str]) -> CommandResult:
        self.calls.append(argv)
        return CommandResult(0, "", "")


def test_local_docker_run_args_include_limits_and_mount(tmp_path: Path) -> None:
    sbx = LocalDockerSandbox("itpr-worker", tmp_path, container_name="c1")
    args = " ".join(sbx.build_run_args())
    assert "docker run -d" in args
    assert "--name c1" in args
    assert "--network none" in args
    assert f"{tmp_path.resolve()}:/workspace" in args
    assert args.strip().endswith("sleep infinity")


def test_local_docker_exec_requires_start(tmp_path: Path) -> None:
    sbx = LocalDockerSandbox("itpr-worker", tmp_path, docker=FakeDocker())
    with pytest.raises(SandboxError):
        sbx.exec(["echo", "hi"])


def test_local_docker_start_exec_teardown(tmp_path: Path) -> None:
    docker = FakeDocker()
    sbx = LocalDockerSandbox("itpr-worker", tmp_path, container_name="c1", docker=docker)
    sbx.start()
    sbx.exec(["pytest", "-q"])
    sbx.teardown()
    assert docker.calls[0][:2] == ["docker", "run"]
    assert docker.calls[1][:3] == ["docker", "exec", "c1"]
    assert docker.calls[-1][:3] == ["docker", "rm", "-f"]


def test_sandbox_session_tears_down_on_exception(tmp_path: Path) -> None:
    docker = FakeDocker()
    sbx = LocalDockerSandbox("itpr-worker", tmp_path, container_name="c1", docker=docker)
    with pytest.raises(RuntimeError):
        with sandbox_session(sbx):
            raise RuntimeError("boom")
    # teardown (docker rm) still ran despite the exception
    assert any(c[:3] == ["docker", "rm", "-f"] for c in docker.calls)


def test_filesystem_write_confined_to_workspace(tmp_path: Path) -> None:
    docker = FakeDocker()
    sbx = LocalDockerSandbox("itpr-worker", tmp_path, docker=docker)
    sbx.write_file("a/b.txt", "data")
    assert (tmp_path / "a" / "b.txt").read_text() == "data"
    with pytest.raises(SafetyRefusal):
        sbx.write_file("../escape.txt", "x")
