"""Produce an initial plan from the issue + repo context."""

from __future__ import annotations

from pathlib import Path

from ..llm.client import LLMClient
from ..llm.provider_base import Message

_PROMPTS = Path(__file__).resolve().parents[1] / "llm" / "prompts"


def _load(name: str) -> str:
    return (_PROMPTS / name).read_text(encoding="utf-8")


def plan(llm: LLMClient, issue: str, context: str) -> str:
    messages = [
        Message("system", _load("system.md")),
        Message("user", f"{_load('plan.md')}\n\n## Issue\n{issue}\n\n## Context\n{context}"),
    ]
    return llm.complete(messages, max_tokens=16384).text
