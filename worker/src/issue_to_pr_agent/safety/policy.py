"""Aggregate safety policy + a single guard the agent routes actions through."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .command_denylist import (
    DEFAULT_DENYLIST,
    assert_command_allowed,
    load_denylist,
)
from .credential_guard import assert_diff_has_no_secrets
from .forbidden_paths import DEFAULT_FORBIDDEN, assert_path_allowed, load_forbidden
from .log_scrubber import scrub
from .no_force_push import assert_no_force_push, assert_not_pushing_protected
from .secret_scanner import assert_no_secrets
from .workflow_write_blocker import assert_not_workflow


@dataclass(slots=True)
class SafetyPolicy:
    forbidden_paths: list[str] = field(default_factory=lambda: list(DEFAULT_FORBIDDEN))
    denied_commands: list[str] = field(default_factory=lambda: list(DEFAULT_DENYLIST))
    protected_branches: set[str] = field(default_factory=lambda: {"main", "master"})


def load_safety_policy(policies_dir: Path) -> SafetyPolicy:
    forbidden = DEFAULT_FORBIDDEN
    denied = DEFAULT_DENYLIST
    fp = policies_dir / "forbidden-paths.yaml"
    dl = policies_dir / "command-denylist.yaml"
    if fp.exists():
        forbidden = load_forbidden(fp)
    if dl.exists():
        denied = load_denylist(dl)
    return SafetyPolicy(forbidden_paths=list(forbidden), denied_commands=list(denied))


class SafetyGuard:
    """Every mutating action is routed through here. Violations raise SafetyRefusal."""

    def __init__(self, policy: SafetyPolicy | None = None) -> None:
        self.policy = policy or SafetyPolicy()

    def guard_write(self, path: str, content: str | None = None) -> None:
        assert_not_workflow(path)
        assert_path_allowed(path, self.policy.forbidden_paths)
        if content is not None:
            assert_no_secrets(content, where=path)

    def guard_command(self, command: str) -> None:
        assert_command_allowed(command, self.policy.denied_commands)

    def guard_git(self, git_args: list[str]) -> None:
        assert_no_force_push(git_args)
        assert_not_pushing_protected(git_args, self.policy.protected_branches)

    def guard_commit_diff(self, diff: str) -> None:
        assert_diff_has_no_secrets(diff)

    def scrub(self, text: str, *, pii: bool = False) -> str:
        return scrub(text, pii=pii)
