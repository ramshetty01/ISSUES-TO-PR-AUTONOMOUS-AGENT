"""Tool registry + the shared ToolContext handed to every tool.

Tools are the agent's action surface. Execution tools go through the sandbox;
git tools through the worker github layer; all file access is path-jailed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ..github.clone import GitRunner
from ..github.client import GitHubClient
from ..job import Repo
from ..sandbox.base import Sandbox

ToolHandler = Callable[..., Any]


@dataclass(slots=True)
class ToolContext:
    sandbox: Sandbox
    repo_dir: Path
    git: GitRunner | None = None
    github: GitHubClient | None = None
    repo: Repo | None = None


@dataclass(slots=True)
class Tool:
    name: str
    description: str
    handler: ToolHandler
    schema: dict[str, Any]
    expose_to_llm: bool = True


class ToolError(Exception):
    """Raised when a tool is called with a bad name or missing collaborators."""


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def names(self) -> list[str]:
        return sorted(self._tools)

    def schemas(self) -> list[dict[str, Any]]:
        """Tool declarations for LLM tool-calling."""
        return [
            {"name": t.name, "description": t.description, "parameters": t.schema}
            for t in self._tools.values()
            if t.expose_to_llm
        ]

    def call(self, tool_name: str, ctx: ToolContext, /, **args: Any) -> Any:
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ToolError(f"unknown tool: {tool_name}")
        return tool.handler(ctx, **args)


def build_default_registry() -> ToolRegistry:
    from . import (
        edit_file,
        git_apply_patch,
        git_diff,
        git_commit,
        git_status,
        github_comment,
        list_files,
        read_file,
        ripgrep,
        run_coverage,
        run_shell,
        run_tests,
        tree_sitter_search,
        write_file,
    )
    from .schemas import TOOL_SCHEMAS

    reg = ToolRegistry()
    modules: dict[str, ToolHandler] = {
        "read_file": read_file.read_file,
        "write_file": write_file.write_file,
        "edit_file": edit_file.edit_file,
        "list_files": list_files.list_files_tool,
        "ripgrep": ripgrep.ripgrep_tool,
        "tree_sitter_search": tree_sitter_search.tree_sitter_search,
        "run_shell": run_shell.run_shell,
        "run_tests": run_tests.run_tests,
        "run_coverage": run_coverage.run_coverage,
        "git_status": git_status.git_status,
        "git_diff": git_diff.git_diff,
        "git_apply_patch": git_apply_patch.git_apply_patch,
        "git_commit": git_commit.git_commit,
        "github_comment": github_comment.github_comment,
    }
    for name, handler in modules.items():
        schema = TOOL_SCHEMAS[name]
        reg.register(
            Tool(
                name,
                schema["description"],
                handler,
                schema["parameters"],
                expose_to_llm=name != "git_commit",
            )
        )
    return reg
