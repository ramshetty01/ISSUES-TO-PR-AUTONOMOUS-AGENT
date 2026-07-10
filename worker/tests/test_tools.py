"""Phase 25 tool tests — fake sandbox (tmp workspace) + fake git, no docker."""

from __future__ import annotations

from pathlib import Path

import pytest

from issue_to_pr_agent.errors import SandboxError
from issue_to_pr_agent.github.clone import GitResult
from issue_to_pr_agent.sandbox.command_runner import CommandResult
from issue_to_pr_agent.sandbox.filesystem import PathJail
from issue_to_pr_agent.tools import (
    ToolContext,
    ToolError,
    build_default_registry,
)


class FakeSandbox:
    """Path-jailed fs on a real tmp dir; exec records commands."""

    def __init__(self, root: Path, exec_result: CommandResult | None = None) -> None:
        self._jail = PathJail(root)
        self._root = root
        self.exec_calls: list[list[str]] = []
        self._exec_result = exec_result or CommandResult(0, "ok", "")

    @property
    def workspace(self) -> Path:
        return self._root

    def start(self) -> None: ...

    def exec(self, argv, *, timeout=None):
        self.exec_calls.append(argv)
        return self._exec_result

    def read_file(self, relpath):
        return self._jail.read_text(relpath)

    def write_file(self, relpath, content):
        self._jail.write_text(relpath, content)

    def teardown(self) -> None: ...


class FakeGit:
    def __init__(self, results=None):
        self.calls: list[list[str]] = []
        self.results = results or {}

    def run(self, args, cwd=None):
        self.calls.append(args)
        return self.results.get(args[0], GitResult(0, "", ""))


def ctx(tmp_path: Path, **kw) -> ToolContext:
    sbx = kw.pop("sandbox", None) or FakeSandbox(tmp_path)
    return ToolContext(sandbox=sbx, repo_dir=tmp_path, **kw)


def test_registry_has_all_tools() -> None:
    reg = build_default_registry()
    assert set(reg.names()) >= {
        "read_file", "write_file", "edit_file", "list_files", "ripgrep",
        "tree_sitter_search", "run_shell", "run_tests", "run_coverage",
        "git_status", "git_diff", "git_apply_patch", "git_commit", "github_comment",
    }
    # every tool has a schema with a description
    for s in reg.schemas():
        assert s["name"] and s["description"] and "parameters" in s


def test_unknown_tool_raises(tmp_path: Path) -> None:
    reg = build_default_registry()
    with pytest.raises(ToolError):
        reg.call("nope", ctx(tmp_path))


def test_write_then_read_then_edit(tmp_path: Path) -> None:
    reg = build_default_registry()
    c = ctx(tmp_path)
    reg.call("write_file", c, path="a/b.py", content="x = 1\n")
    assert reg.call("read_file", c, path="a/b.py")["content"] == "x = 1\n"
    reg.call("edit_file", c, path="a/b.py", old="x = 1", new="x = 2")
    assert "x = 2" in reg.call("read_file", c, path="a/b.py")["content"]


def test_edit_file_missing_old(tmp_path: Path) -> None:
    reg = build_default_registry()
    c = ctx(tmp_path)
    reg.call("write_file", c, path="f.py", content="hello\n")
    with pytest.raises(SandboxError):
        reg.call("edit_file", c, path="f.py", old="nope", new="x")


def test_write_outside_jail_refused(tmp_path: Path) -> None:
    reg = build_default_registry()
    from issue_to_pr_agent.errors import SafetyRefusal

    with pytest.raises(SafetyRefusal):
        reg.call("write_file", ctx(tmp_path), path="../escape.txt", content="x")


def test_list_and_search(tmp_path: Path) -> None:
    reg = build_default_registry()
    c = ctx(tmp_path)
    reg.call("write_file", c, path="src/calc.py", content="def add(a, b):\n    return a + b\n")
    listing = reg.call("list_files", c)
    assert "src/calc.py" in listing["files"]
    rg = reg.call("ripgrep", c, pattern="def add")
    assert any(m["file"] == "src/calc.py" for m in rg["matches"])
    ts = reg.call("tree_sitter_search", c, name="add")
    assert ts["symbols"][0]["file"] == "src/calc.py"


def test_run_shell_via_sandbox(tmp_path: Path) -> None:
    reg = build_default_registry()
    sbx = FakeSandbox(tmp_path, exec_result=CommandResult(0, "3 passed", ""))
    c = ctx(tmp_path, sandbox=sbx)
    res = reg.call("run_tests", c, command="pytest")
    assert res["ok"] is True
    assert sbx.exec_calls[0] == ["sh", "-c", "pytest"]


def test_git_tools(tmp_path: Path) -> None:
    reg = build_default_registry()
    git = FakeGit({
        "status": GitResult(0, " M src/calc.py\n", ""),
        "diff": GitResult(0, "diff --git a b\n", ""),
        "rev-parse": GitResult(0, "deadbeef\n", ""),
    })
    c = ctx(tmp_path, git=git)
    assert reg.call("git_status", c)["changed"] == [" M src/calc.py"]
    assert "diff --git" in reg.call("git_diff", c)["diff"]
    assert reg.call("git_commit", c, message="fix")["sha"] == "deadbeef"


def test_git_tool_requires_runner(tmp_path: Path) -> None:
    reg = build_default_registry()
    with pytest.raises(SandboxError):
        reg.call("git_status", ctx(tmp_path))  # no git in context


def test_git_apply_patch_validates(tmp_path: Path) -> None:
    reg = build_default_registry()
    # first `apply` call is --check; make it fail
    git = FakeGit({"apply": GitResult(1, "", "does not apply")})
    with pytest.raises(SandboxError):
        reg.call("git_apply_patch", ctx(tmp_path, git=git), patch="bad patch")
