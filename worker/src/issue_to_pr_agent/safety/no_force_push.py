"""Refuse force pushes and pushes to protected branches at the git-args level."""

from __future__ import annotations

from .refusal import refuse

_FORCE_FLAGS = {"--force", "-f", "--force-with-lease"}


def is_force_push(git_args: list[str]) -> bool:
    return git_args[:1] == ["push"] and any(a in _FORCE_FLAGS for a in git_args)


def assert_no_force_push(git_args: list[str]) -> None:
    if is_force_push(git_args):
        raise refuse("force_push_blocked", "force push is not allowed", " ".join(git_args))


def assert_not_pushing_protected(git_args: list[str], protected: set[str]) -> None:
    """Refuse `git push origin <protected>`."""
    if git_args[:1] != ["push"]:
        return
    for a in git_args[2:]:  # skip "push" + remote
        branch = a.split(":")[-1]
        if branch in protected:
            raise refuse(
                "workflow_write_blocked", "cannot push to a protected branch", branch
            )
