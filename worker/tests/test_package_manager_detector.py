"""Phase 21 package-manager + test-command detection tests."""

from __future__ import annotations

from pathlib import Path

from issue_to_pr_agent.inference.package_manager_detector import detect_package_manager
from issue_to_pr_agent.inference.test_command_detector import detect_test_command


def write(repo: Path, name: str, content: str = "") -> None:
    (repo / name).write_text(content, encoding="utf-8")


def test_python_uv(tmp_path: Path) -> None:
    write(tmp_path, "uv.lock")
    assert detect_package_manager(tmp_path, "python") == "uv"


def test_python_poetry_lock(tmp_path: Path) -> None:
    write(tmp_path, "poetry.lock")
    assert detect_package_manager(tmp_path, "python") == "poetry"


def test_python_poetry_table(tmp_path: Path) -> None:
    write(tmp_path, "pyproject.toml", "[tool.poetry]\nname='x'\n")
    assert detect_package_manager(tmp_path, "python") == "poetry"


def test_python_pip_default(tmp_path: Path) -> None:
    write(tmp_path, "requirements.txt", "pytest\n")
    assert detect_package_manager(tmp_path, "python") == "pip"


def test_node_pnpm(tmp_path: Path) -> None:
    write(tmp_path, "pnpm-lock.yaml")
    assert detect_package_manager(tmp_path, "node") == "pnpm"


def test_node_yarn(tmp_path: Path) -> None:
    write(tmp_path, "yarn.lock")
    assert detect_package_manager(tmp_path, "node") == "yarn"


def test_node_npm_default(tmp_path: Path) -> None:
    assert detect_package_manager(tmp_path, "node") == "npm"


def test_java_maven_vs_gradle(tmp_path: Path) -> None:
    write(tmp_path, "pom.xml")
    assert detect_package_manager(tmp_path, "java") == "maven"


def test_test_commands() -> None:
    assert detect_test_command("python", "pip", "pytest") == "pytest"
    assert detect_test_command("node", "pnpm", None) == "pnpm test"
    assert detect_test_command("go", "go", None) == "go test ./..."
    assert detect_test_command("rust", "cargo", None) == "cargo test"
    assert detect_test_command("java", "maven", None) == "mvn test"
    assert detect_test_command("java", "gradle", None) == "./gradlew test"
