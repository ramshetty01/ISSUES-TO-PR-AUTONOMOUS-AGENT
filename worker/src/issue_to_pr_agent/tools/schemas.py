"""JSON schemas for tool-calling (declarations exposed to the LLM)."""

from __future__ import annotations

from typing import Any


def _obj(props: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": props, "required": required}


_STR = {"type": "string"}
_INT = {"type": "integer"}

TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "read_file": {
        "description": "Read a file's contents (path relative to the repo root).",
        "parameters": _obj({"path": _STR}, ["path"]),
    },
    "write_file": {
        "description": "Overwrite a file with new contents.",
        "parameters": _obj({"path": _STR, "content": _STR}, ["path", "content"]),
    },
    "edit_file": {
        "description": "Replace one exact, unique substring in a file.",
        "parameters": _obj({"path": _STR, "old": _STR, "new": _STR}, ["path", "old", "new"]),
    },
    "list_files": {
        "description": "List repository files, skipping noise directories.",
        "parameters": _obj({"max_files": _INT}, []),
    },
    "ripgrep": {
        "description": "Search file contents for a regex pattern.",
        "parameters": _obj({"pattern": _STR, "max_results": _INT}, ["pattern"]),
    },
    "tree_sitter_search": {
        "description": "Find symbol definitions (functions/classes) by name.",
        "parameters": _obj({"name": _STR}, ["name"]),
    },
    "run_shell": {
        "description": "Run a shell command inside the sandbox.",
        "parameters": _obj({"command": _STR, "timeout": {"type": "number"}}, ["command"]),
    },
    "run_tests": {
        "description": "Run the repository's test command inside the sandbox.",
        "parameters": _obj({"command": _STR, "timeout": {"type": "number"}}, ["command"]),
    },
    "run_coverage": {
        "description": "Run the repository's coverage command inside the sandbox.",
        "parameters": _obj({"command": _STR, "timeout": {"type": "number"}}, ["command"]),
    },
    "git_status": {
        "description": "Show the working-tree status (porcelain).",
        "parameters": _obj({}, []),
    },
    "git_diff": {
        "description": "Show the current diff, optionally vs a base ref.",
        "parameters": _obj({"base": _STR}, []),
    },
    "git_apply_patch": {
        "description": "Apply a unified-diff patch atomically (validated first).",
        "parameters": _obj({"patch": _STR}, ["patch"]),
    },
    "git_commit": {
        "description": "Stage all changes and commit with the app identity.",
        "parameters": _obj({"message": _STR}, ["message"]),
    },
    "github_comment": {
        "description": "Post a comment on the triggering issue or pull request.",
        "parameters": _obj({"issue_number": _INT, "body": _STR}, ["issue_number", "body"]),
    },
}
