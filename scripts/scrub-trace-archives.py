#!/usr/bin/env python3
"""Redact secrets (and optionally PII) from stored trace archives.

Standalone, stdlib-only mirror of the worker's
``issue_to_pr_agent.safety.log_scrubber`` so it can run against exported traces
without installing the worker package. Patterns are kept in sync with
``worker/src/issue_to_pr_agent/safety/{secret_scanner,pii_scanner}.py``.

Usage:
    scrub-trace-archives.py [--pii] [--in-place | -o OUT] PATH [PATH ...]

PATH may be a file (``.json``, ``.jsonl``, ``.log``, ``.txt``) or a directory
(scanned recursively). ``.json``/``.jsonl`` files are parsed and scrubbed
value-by-value so structure is preserved; other text files are scrubbed
line-oriented. Redaction is idempotent: placeholders never re-match.

Exit status is 0 on success, 1 on usage/IO error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# --- patterns (kept in sync with the worker safety scanners) ----------------

SECRET_PATTERNS: list[tuple[str, "re.Pattern[str]"]] = [
    (
        "private_key",
        re.compile(
            r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----[\s\S]*?"
            r"-----END (?:[A-Z]+ )?PRIVATE KEY-----"
        ),
    ),
    ("github_token", re.compile(r"\bgh[opusr]_[A-Za-z0-9]{36}\b")),
    ("github_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{60,}\b")),
    ("aws_access_key_id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/\-]{10,}=*")),
    (
        "generic_secret",
        re.compile(
            r"\b(?:api[_-]?key|secret|token|password|passwd|access[_-]?key)\b"
            r"\s*[:=]\s*['\"]?[A-Za-z0-9._\-]{12,}",
            re.IGNORECASE,
        ),
    ),
]

PII_PATTERNS: list[tuple[str, "re.Pattern[str]"]] = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    (
        "ipv4",
        re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
        ),
    ),
    (
        "phone",
        re.compile(
            r"(?<!\d)(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)"
        ),
    ),
]

TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".ndjson"}


def _placeholder(kind: str) -> str:
    return f"[REDACTED:{kind}]"


def scrub_text(text: str, *, pii: bool = False) -> str:
    """Redact secrets (and optionally PII) from a string. Idempotent."""
    out = text
    for kind, rx in SECRET_PATTERNS:
        out = rx.sub(_placeholder(kind), out)
    if pii:
        for kind, rx in PII_PATTERNS:
            out = rx.sub(_placeholder(kind), out)
    return out


def scrub_deep(value: Any, *, pii: bool = False) -> Any:
    """Recursively scrub strings inside parsed JSON structures."""
    if isinstance(value, str):
        return scrub_text(value, pii=pii)
    if isinstance(value, list):
        return [scrub_deep(v, pii=pii) for v in value]
    if isinstance(value, dict):
        return {k: scrub_deep(v, pii=pii) for k, v in value.items()}
    return value


def scrub_json_document(raw: str, *, pii: bool = False) -> str:
    """Scrub a JSON document; fall back to text scrubbing if it doesn't parse."""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return scrub_text(raw, pii=pii)
    return json.dumps(scrub_deep(parsed, pii=pii), indent=2, ensure_ascii=False)


def scrub_jsonl_document(raw: str, *, pii: bool = False) -> str:
    """Scrub each line of a JSON-lines document independently."""
    out_lines: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            out_lines.append(line)
            continue
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            out_lines.append(scrub_text(line, pii=pii))
            continue
        out_lines.append(json.dumps(scrub_deep(parsed, pii=pii), ensure_ascii=False))
    return "\n".join(out_lines)


def scrub_file_content(path: Path, raw: str, *, pii: bool) -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return scrub_json_document(raw, pii=pii)
    if suffix in {".jsonl", ".ndjson"}:
        return scrub_jsonl_document(raw, pii=pii)
    return scrub_text(raw, pii=pii)


def iter_target_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(
                f for f in sorted(p.rglob("*")) if f.is_file() and f.suffix.lower() in TEXT_SUFFIXES
            )
        elif p.is_file():
            files.append(p)
        else:
            print(f"!! not found: {p}", file=sys.stderr)
    return files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scrub-trace-archives.py",
        description="Redact secrets (and optionally PII) from stored trace archives.",
    )
    parser.add_argument("paths", nargs="+", type=Path, help="file(s) or directory(ies) to scrub")
    parser.add_argument(
        "--pii", action="store_true", help="also redact PII (emails, IPv4, phone numbers)"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--in-place", action="store_true", help="overwrite inputs with scrubbed content"
    )
    group.add_argument(
        "-o",
        "--out",
        type=Path,
        help="write a single scrubbed file here (only valid for a single input file)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 2 if any file would change (no writes); useful in CI",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    files = iter_target_files(args.paths)
    if not files:
        print("!! no matching files to scrub", file=sys.stderr)
        return 1

    if args.out is not None and (len(files) != 1 or args.paths[0].is_dir()):
        print("!! -o/--out requires exactly one input file", file=sys.stderr)
        return 1

    changed = 0
    for f in files:
        try:
            raw = f.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"!! cannot read {f}: {exc}", file=sys.stderr)
            return 1
        scrubbed = scrub_file_content(f, raw, pii=args.pii)
        will_change = scrubbed != raw
        if will_change:
            changed += 1

        if args.check:
            if will_change:
                print(f"would scrub: {f}")
            continue

        if args.out is not None:
            args.out.write_text(scrubbed, encoding="utf-8")
            print(f"scrubbed {f} -> {args.out}")
        elif args.in_place:
            if will_change:
                f.write_text(scrubbed, encoding="utf-8")
            print(f"scrubbed{' (no change)' if not will_change else ''}: {f}")
        else:
            # Default: print to stdout (single file) or a header-prefixed dump.
            if len(files) > 1:
                print(f"===== {f} =====")
            sys.stdout.write(scrubbed)
            if not scrubbed.endswith("\n"):
                sys.stdout.write("\n")

    if args.check and changed:
        print(f"!! {changed} file(s) contain unredacted secrets/PII", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
