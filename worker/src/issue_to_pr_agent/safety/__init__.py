"""Safety layer: the hard boundary (20% of the rubric)."""

from ..errors import SafetyRefusal
from .command_denylist import assert_command_allowed, find_denied
from .credential_guard import assert_diff_has_no_secrets
from .forbidden_paths import assert_path_allowed, is_forbidden
from .log_scrubber import scrub, scrub_deep
from .no_force_push import (
    assert_no_force_push,
    assert_not_pushing_protected,
    is_force_push,
)
from .path_jail import assert_within_jail, is_within_jail
from .pii_scanner import scan_pii
from .policy import SafetyGuard, SafetyPolicy, load_safety_policy
from .refusal import Refusal, refuse
from .secret_scanner import assert_no_secrets, has_secret, scan_secrets
from .workflow_write_blocker import assert_not_workflow, is_workflow_path

__all__ = [
    "SafetyRefusal",
    "SafetyGuard",
    "SafetyPolicy",
    "load_safety_policy",
    "Refusal",
    "refuse",
    "assert_command_allowed",
    "find_denied",
    "assert_diff_has_no_secrets",
    "assert_path_allowed",
    "is_forbidden",
    "scrub",
    "scrub_deep",
    "assert_no_force_push",
    "assert_not_pushing_protected",
    "is_force_push",
    "assert_within_jail",
    "is_within_jail",
    "scan_pii",
    "assert_no_secrets",
    "has_secret",
    "scan_secrets",
    "assert_not_workflow",
    "is_workflow_path",
]
