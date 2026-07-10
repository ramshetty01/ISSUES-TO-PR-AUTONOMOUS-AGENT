"""Repo inference + Dockerfile synthesis (core capstone value)."""

from .detector import detect
from .repo_facts import RepoFacts, detect_repo_facts
from .language_detector import detect_language
from .package_manager_detector import detect_package_manager
from .framework_detector import detect_framework
from .test_command_detector import detect_test_command
from .coverage_detector import detect_coverage_command
from .dockerfile_synthesizer import select_template, synthesize_dockerfile
from .docker_build import BuildResult, build_image

__all__ = [
    "detect",
    "RepoFacts",
    "detect_repo_facts",
    "detect_language",
    "detect_package_manager",
    "detect_framework",
    "detect_test_command",
    "detect_coverage_command",
    "select_template",
    "synthesize_dockerfile",
    "BuildResult",
    "build_image",
]
