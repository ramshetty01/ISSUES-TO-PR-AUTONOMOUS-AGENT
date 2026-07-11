"""Phase 24 agent-loop tests — scripted provider, fake sandbox; zero real tokens."""

from __future__ import annotations

from pathlib import Path

from issue_to_pr_agent.agent import (
    AgentController,
    TurnBudget,
    action_json,
    parse_action,
    run_agent,
)
from issue_to_pr_agent.agent.observation_budget import ObservationBudget
from issue_to_pr_agent.llm.client import LLMClient
from issue_to_pr_agent.llm.provider_base import Completion, Provider, TokenUsage
from issue_to_pr_agent.llm.router import Router
from issue_to_pr_agent.sandbox.command_runner import CommandResult
from issue_to_pr_agent.sandbox.filesystem import PathJail
from issue_to_pr_agent.tools import ToolContext, build_default_registry


class ScriptedProvider(Provider):
    """Returns queued responses; repeats the last once the queue drains."""

    name = "scripted"

    def __init__(self, responses: list[str]) -> None:
        self._q = list(responses)
        self._default = responses[-1]

    def complete(self, messages, *, max_tokens=1024, temperature=0.2) -> Completion:
        text = self._q.pop(0) if self._q else self._default
        return Completion(text, TokenUsage(1, 1), self.name)


class FakeSandbox:
    def __init__(self, root: Path) -> None:
        self._jail = PathJail(root)
        self._root = root

    @property
    def workspace(self) -> Path:
        return self._root

    def start(self) -> None: ...

    def exec(self, argv, *, timeout=None):
        return CommandResult(0, "ok", "")

    def read_file(self, relpath):
        return self._jail.read_text(relpath)

    def write_file(self, relpath, content):
        self._jail.write_text(relpath, content)

    def teardown(self) -> None: ...


def client(responses: list[str]) -> LLMClient:
    return LLMClient(Router([ScriptedProvider(responses)]))


def ctx(tmp_path: Path) -> ToolContext:
    return ToolContext(sandbox=FakeSandbox(tmp_path), repo_dir=tmp_path)


def test_parse_action_variants() -> None:
    assert parse_action('{"tool":"read_file","args":{"path":"a"}}').kind == "tool"
    assert parse_action('{"finish":true,"success":true}').kind == "finish"
    assert parse_action("not json").kind == "invalid"


def test_loop_writes_then_finishes(tmp_path: Path) -> None:
    llm = client([
        "PLAN: write the file",
        action_json("write_file", {"path": "a.py", "content": "x = 1\n"}),
        action_json(finish=True, success=True),
    ])
    result = run_agent(llm, build_default_registry(), ctx(tmp_path), "add a.py")
    assert result.success is True
    assert result.turns == 2
    assert (tmp_path / "a.py").read_text() == "x = 1\n"
    assert result.stop_reason == "finished"


def test_loop_exposes_tool_contract_to_model(tmp_path: Path) -> None:
    provider = ScriptedProvider([
        "PLAN",
        action_json(finish=True, success=False),
    ])
    captured = []
    original_complete = provider.complete

    def record(messages, *, max_tokens=1024, temperature=0.2):
        captured.append((messages, max_tokens))
        return original_complete(
            messages, max_tokens=max_tokens, temperature=temperature
        )

    provider.complete = record  # type: ignore[method-assign]
    llm = LLMClient(Router([provider]))

    run_agent(llm, build_default_registry(), ctx(tmp_path), "edit a file")

    action_messages, max_tokens = captured[1]
    prompt = action_messages[-1].content
    assert "## Available tools" in prompt
    assert '"name": "edit_file"' in prompt
    assert '"old"' in prompt
    assert max_tokens == 16384


def test_loop_tool_failure_is_recoverable(tmp_path: Path) -> None:
    llm = client([
        "PLAN",
        action_json("edit_file", {"path": "missing.py", "old": "x", "new": "y"}),  # fails
        action_json(finish=True, success=True),
    ])
    result = run_agent(llm, build_default_registry(), ctx(tmp_path), "edit")
    assert result.success is True
    assert any("failed" in o for o in result.state.observations)


def test_turn_budget_stops_runaway_loop(tmp_path: Path) -> None:
    # never finishes: keeps writing
    llm = client([
        "PLAN",
        action_json("write_file", {"path": "a.py", "content": "x\n"}),
    ])
    result = run_agent(
        llm,
        build_default_registry(),
        ctx(tmp_path),
        "loop",
        turn_budget=TurnBudget(max_turns=3),
    )
    assert result.success is False
    assert result.turns == 3
    assert result.stop_reason == "turn_budget_exceeded"


def test_too_many_invalid_actions_stops(tmp_path: Path) -> None:
    llm = client(["PLAN", "garbage-not-json"])
    result = run_agent(llm, build_default_registry(), ctx(tmp_path), "x")
    assert result.success is False
    assert result.stop_reason == "too_many_failures"


def test_observation_budget_trims(tmp_path: Path) -> None:
    ob = ObservationBudget(max_tokens=10)
    long = ["x" * 100, "y" * 100, "z" * 5]
    trimmed = ob.trim(long)
    assert ob.total(trimmed) <= 10
    assert trimmed[-1] == "z" * 5  # keeps the most recent


def test_controller_runs_deterministically(tmp_path: Path) -> None:
    script = [
        "PLAN",
        action_json("write_file", {"path": "a.py", "content": "1\n"}),
        action_json(finish=True, success=True),
    ]
    r1 = AgentController(client(script), build_default_registry()).run(ctx(tmp_path), "x")
    r2 = AgentController(client(script), build_default_registry()).run(ctx(tmp_path), "x")
    assert (r1.success, r1.turns) == (r2.success, r2.turns) == (True, 2)
