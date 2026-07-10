"""Specifically block writes to GitHub Actions workflow files."""

from __future__ import annotations

from .refusal import refuse

WORKFLOW_PREFIXES = (".github/workflows/", ".github/actions/")


def is_workflow_path(path: str) -> bool:
    norm = path[2:] if path.startswith("./") else path
    return norm.startswith(WORKFLOW_PREFIXES)


def assert_not_workflow(path: str) -> None:
    if is_workflow_path(path):
        raise refuse("workflow_write_blocked", "cannot modify CI workflows", path)
