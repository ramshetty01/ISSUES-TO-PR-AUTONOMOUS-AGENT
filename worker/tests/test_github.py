"""Phase 19 worker github tests — fake GitRunner + fake transport (no network)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from issue_to_pr_agent.errors import SafetyRefusal, SandboxError
from issue_to_pr_agent.github.clone import GitResult, authed_url, clone_repo
from issue_to_pr_agent.github.branches import create_branch, current_branch, push_branch
from issue_to_pr_agent.github.commits import commit_all
from issue_to_pr_agent.github.client import GitHubClient
from issue_to_pr_agent.github.pull_requests import open_pull
from issue_to_pr_agent.github.labels import apply_labels
from issue_to_pr_agent.github.branch_protection import assert_not_protected, is_protected
from issue_to_pr_agent.job import Repo

REPO = Repo(owner="acme", name="widgets")


class FakeGit:
    """Records commands; returns a scripted result per first-arg subcommand."""

    def __init__(self, results: dict[str, GitResult] | None = None) -> None:
        self.calls: list[list[str]] = []
        self.results = results or {}

    def run(self, args: list[str], cwd: Path | None = None) -> GitResult:
        self.calls.append(args)
        return self.results.get(args[0], GitResult(0, "", ""))


def test_authed_url_embeds_token() -> None:
    url = authed_url(REPO, "ghs_secret")
    assert url == "https://x-access-token:ghs_secret@github.com/acme/widgets.git"


def test_clone_runs_git_clone(tmp_path: Path) -> None:
    git = FakeGit()
    clone_repo(git, REPO, "ghs_secret", tmp_path / "repo")
    assert git.calls[0][0] == "clone"


def test_clone_failure_hides_token(tmp_path: Path) -> None:
    git = FakeGit({"clone": GitResult(128, "", "auth error")})
    with pytest.raises(SandboxError) as exc:
        clone_repo(git, REPO, "ghs_secret", tmp_path / "repo")
    assert "ghs_secret" not in str(exc.value)


def test_create_branch_and_current() -> None:
    git = FakeGit({"rev-parse": GitResult(0, "fix/bug\n", "")})
    assert create_branch(git, Path("/repo"), "fix/bug") == "fix/bug"
    assert current_branch(git, Path("/repo")) == "fix/bug"


def test_push_refuses_protected_branch() -> None:
    git = FakeGit()
    with pytest.raises(SafetyRefusal):
        push_branch(git, Path("/repo"), "main", protected={"main"})


def test_push_refuses_force() -> None:
    git = FakeGit()
    with pytest.raises(SafetyRefusal):
        push_branch(git, Path("/repo"), "fix/bug", protected=set(), force=True)


def test_push_ok_feature_branch() -> None:
    git = FakeGit()
    push_branch(git, Path("/repo"), "fix/bug", protected={"main"})
    assert ["push", "origin", "fix/bug"] in git.calls


def test_commit_all_returns_sha() -> None:
    git = FakeGit({"rev-parse": GitResult(0, "deadbeef\n", "")})
    sha = commit_all(git, Path("/repo"), "fix things")
    assert sha == "deadbeef"
    # identity configured with the bot author
    assert any(c[:2] == ["config", "user.name"] for c in git.calls)


# ---- API client (fake transport) ----

def make_transport(responses: dict[tuple[str, str], tuple[int, Any]]):
    calls: list[tuple[str, str, dict[str, str], bytes | None]] = []

    def transport(method: str, url: str, headers: dict[str, str], body: bytes | None):
        calls.append((method, url, headers, body))
        for (m, frag), resp in responses.items():
            if m == method and frag in url:
                return resp
        return 404, None

    return transport, calls


def test_open_pull_posts_and_returns_url() -> None:
    transport, calls = make_transport(
        {("POST", "/pulls"): (201, {"number": 12, "html_url": "https://x/pull/12"})}
    )
    client = GitHubClient("ghs_x", transport)
    res = open_pull(client, REPO, title="Fix", head="fix/bug", base="main", body="b")
    assert res == {"number": 12, "url": "https://x/pull/12"}
    # auth header present, correct endpoint
    assert calls[0][2]["Authorization"] == "Bearer ghs_x"


def test_apply_labels_noop_on_empty() -> None:
    transport, calls = make_transport({})
    client = GitHubClient("ghs_x", transport)
    apply_labels(client, REPO, 1, [])
    assert calls == []


def test_branch_protection_detection() -> None:
    transport, _ = make_transport(
        {("GET", "/branches/main/protection"): (200, {"required_pull_request_reviews": {}})}
    )
    client = GitHubClient("ghs_x", transport)
    assert is_protected(client, REPO, "main") is True


def test_branch_protection_absent_is_false() -> None:
    transport, _ = make_transport({("GET", "/protection"): (404, None)})
    client = GitHubClient("ghs_x", transport)
    assert is_protected(client, REPO, "main") is False


def test_assert_not_protected_guard() -> None:
    assert_not_protected("fix/bug", {"main"})  # ok
    with pytest.raises(SafetyRefusal):
        assert_not_protected("main", {"main"})
