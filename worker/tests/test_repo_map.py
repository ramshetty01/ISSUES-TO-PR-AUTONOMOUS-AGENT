"""Phase 22 repo-map + context-pack tests (fixture repo in tmp_path)."""

from __future__ import annotations

from pathlib import Path

from issue_to_pr_agent.github.clone import GitResult
from issue_to_pr_agent.repo_map import (
    build_context_pack,
    build_dependency_graph,
    build_symbol_graph,
    changed_files,
    estimate_tokens,
    list_files,
    search,
)


def make_repo(root: Path) -> None:
    (root / "src").mkdir()
    (root / "src" / "calc.py").write_text(
        "import os\n\n\ndef add(a, b):\n    return a + b\n\n\nclass Calculator:\n    pass\n",
        encoding="utf-8",
    )
    (root / "src" / "main.py").write_text(
        "from src.calc import add\n\n\ndef run():\n    return add(1, 2)\n",
        encoding="utf-8",
    )
    # noise that must be skipped
    (root / ".git").mkdir()
    (root / ".git" / "HEAD").write_text("ref: x", encoding="utf-8")
    (root / "node_modules").mkdir()
    (root / "node_modules" / "junk.js").write_text("noise", encoding="utf-8")


def test_list_files_skips_noise(tmp_path: Path) -> None:
    make_repo(tmp_path)
    files = {str(p) for p in list_files(tmp_path)}
    assert "src/calc.py" in files
    assert "src/main.py" in files
    assert not any(".git" in f or "node_modules" in f for f in files)


def test_search_finds_symbol(tmp_path: Path) -> None:
    make_repo(tmp_path)
    matches = search(tmp_path, "def add")
    assert any(m.file == "src/calc.py" for m in matches)


def test_symbol_graph_resolves(tmp_path: Path) -> None:
    make_repo(tmp_path)
    graph = build_symbol_graph(tmp_path)
    add = graph.lookup("add")
    assert add and add[0].file == "src/calc.py"
    assert graph.lookup("Calculator")[0].kind == "class"
    assert graph.lookup("missing") == []


def test_dependency_graph_edges(tmp_path: Path) -> None:
    make_repo(tmp_path)
    graph = build_dependency_graph(tmp_path)
    assert "os" in graph["src/calc.py"]
    assert "src" in graph["src/main.py"]


def test_changed_files_via_git(tmp_path: Path) -> None:
    class FakeGit:
        def run(self, args: list[str], cwd: Path | None = None) -> GitResult:
            return GitResult(0, "src/calc.py\nsrc/main.py\n", "")

    assert changed_files(FakeGit(), tmp_path, "HEAD~1") == ["src/calc.py", "src/main.py"]


def test_context_pack_respects_token_budget(tmp_path: Path) -> None:
    make_repo(tmp_path)
    # tiny budget: pack must stay under it
    pack = build_context_pack(tmp_path, "add calculator", budget_tokens=40)
    assert pack.tokens <= 40


def test_context_pack_prioritizes_changed(tmp_path: Path) -> None:
    make_repo(tmp_path)
    pack = build_context_pack(
        tmp_path, "unrelated query", budget_tokens=8000, changed=["src/main.py"]
    )
    assert "src/main.py" in pack.files
    assert pack.tokens > 0
    # per-block ceil summed is within a few tokens of the whole-text estimate
    assert pack.tokens >= estimate_tokens(pack.text)
