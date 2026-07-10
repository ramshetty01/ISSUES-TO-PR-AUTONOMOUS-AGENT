"""Phase 21 language + framework detection tests."""

from __future__ import annotations

from pathlib import Path

from issue_to_pr_agent.inference.framework_detector import detect_framework
from issue_to_pr_agent.inference.language_detector import detect_language


def write(repo: Path, name: str, content: str = "") -> None:
    (repo / name).write_text(content, encoding="utf-8")


def test_detect_python(tmp_path: Path) -> None:
    write(tmp_path, "pyproject.toml", "[project]\nname='x'\n")
    assert detect_language(tmp_path) == "python"


def test_detect_node(tmp_path: Path) -> None:
    write(tmp_path, "package.json", "{}")
    assert detect_language(tmp_path) == "node"


def test_detect_go(tmp_path: Path) -> None:
    write(tmp_path, "go.mod", "module x\n")
    assert detect_language(tmp_path) == "go"


def test_detect_rust(tmp_path: Path) -> None:
    write(tmp_path, "Cargo.toml", "[package]\n")
    assert detect_language(tmp_path) == "rust"


def test_detect_java_maven(tmp_path: Path) -> None:
    write(tmp_path, "pom.xml", "<project/>")
    assert detect_language(tmp_path) == "java"


def test_detect_unknown(tmp_path: Path) -> None:
    write(tmp_path, "README.md", "# hi")
    assert detect_language(tmp_path) == "unknown"


def test_detect_python_by_source(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    write(tmp_path / "src", "main.py", "print(1)")
    assert detect_language(tmp_path) == "python"


def test_framework_python_default_pytest(tmp_path: Path) -> None:
    write(tmp_path, "pyproject.toml", "[project]\n")
    assert detect_framework(tmp_path, "python") == "pytest"


def test_framework_node_vitest(tmp_path: Path) -> None:
    write(tmp_path, "package.json", '{"devDependencies":{"vitest":"^2"}}')
    assert detect_framework(tmp_path, "node") == "vitest"
