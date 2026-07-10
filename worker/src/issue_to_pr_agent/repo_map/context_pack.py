"""Assemble a token-bounded context pack for the LLM.

Ranking: changed files first (most relevant to the issue), then files whose
contents match keywords from the issue text. Snippets are added until the token
budget is exhausted, so the pack never exceeds the cap.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import ripgrep


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token)."""
    return math.ceil(len(text) / 4)


@dataclass(slots=True)
class ContextPack:
    files: list[str] = field(default_factory=list)
    text: str = ""
    tokens: int = 0


def _keywords(query: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[A-Za-z_]{3,}", query)
    seen: list[str] = []
    for w in words:
        if w.lower() not in {x.lower() for x in seen}:
            seen.append(w)
        if len(seen) >= limit:
            break
    return seen


def _rank_candidates(
    repo_dir: Path, query: str, changed: list[str] | None
) -> list[str]:
    ranked: list[str] = list(changed or [])
    for kw in _keywords(query):
        for m in ripgrep.search(repo_dir, re.escape(kw), max_results=20):
            if m.file not in ranked:
                ranked.append(m.file)
    return ranked


def build_context_pack(
    repo_dir: Path,
    query: str,
    *,
    budget_tokens: int = 8000,
    changed: list[str] | None = None,
    max_lines_per_file: int = 200,
) -> ContextPack:
    pack = ContextPack()
    for rel in _rank_candidates(repo_dir, query, changed):
        path = repo_dir / rel
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        snippet = "\n".join(content.splitlines()[:max_lines_per_file])
        block = f"# file: {rel}\n{snippet}\n"
        block_tokens = estimate_tokens(block)
        if pack.tokens + block_tokens > budget_tokens:
            continue  # skip this one; a smaller later file may still fit
        pack.files.append(rel)
        pack.text += block
        pack.tokens += block_tokens
    return pack
