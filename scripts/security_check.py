#!/usr/bin/env python3
"""Scan tracked and unignored local files for common secret patterns."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path, PurePosixPath


SECRET_PATTERNS = {
    "openai_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "azure_openai_key_assignment": re.compile(
        r"\bAZURE_OPENAI_API_KEY\s*=\s*[\"']?(?!\.\.\.|your-key|your[_-]?key)([A-Za-z0-9+/=_-]{20,})[\"']?",
        re.IGNORECASE,
    ),
    "github_pat": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    "github_classic_pat": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "bearer_token": re.compile(r"\bBearer\s+[A-Za-z0-9._-]{30,}\b"),
    "private_key_block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}

ALLOWLIST_PATTERNS = {
    "env_var_reference": re.compile(r"\bOPENAI_API_KEY\b"),
    "placeholder_key": re.compile(r"your[_-]?(api[_-]?)?key|your_api_key_here", re.IGNORECASE),
}

PRIVATE_EXACT_PATHS = {
    "profile/facts.md",
    "profile/application_answers.json",
    "profile/search_criteria.md",
    "profile/portals.yml",
    "profile/evidence_map.private.json",
    "profile/resume_variants.private.json",
    "jobs/queue.csv",
    "tracker/applications.csv",
}

PRIVATE_PATH_GLOBS = (
    "resumes/*.docx",
    "resumes/*.pdf",
    "jobs/*.txt",
    "jobs/**/*.txt",
    "jobs/*.json",
    "jobs/**/*.json",
    "jobs/*.db",
    "jobs/**/*.db",
    "jobs/*.db-*",
    "jobs/**/*.db-*",
    "data/*.db",
    "data/*.db-*",
    "applications/*",
    "tailored_resumes/*",
    "outputs/*",
    "logs/*",
    "tmp/*",
    "backups/*",
    "browser_state/*",
    "screenshots/*",
    ".secrets/*",
    "docs/research/*",
    "process-map-site/*",
)


def git_paths() -> list[Path]:
    commands = [
        ["git", "ls-files"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    paths: list[Path] = []
    for command in commands:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        paths.extend(Path(line) for line in result.stdout.splitlines() if line.strip())
    return sorted(set(paths))


def history_paths() -> list[Path]:
    """Return every path reachable from the repository's local Git refs."""
    result = subprocess.run(
        ["git", "rev-list", "--objects", "--all"],
        check=True,
        capture_output=True,
        text=True,
    )
    paths = []
    for line in result.stdout.splitlines():
        if " " in line:
            paths.append(Path(line.split(" ", 1)[1]))
    return sorted(set(paths))


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts & {".git", ".venv", "__pycache__"}) or path.suffix.lower() in {
        ".docx",
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".exe",
        ".dll",
        ".pyd",
    }


def mask(value: str) -> str:
    if len(value) <= 12:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def private_path_reason(path: Path) -> str | None:
    """Return a privacy-boundary finding for a path that must stay local."""
    relative = path.as_posix().lstrip("./")
    candidates = [relative]
    if relative.startswith("resume-optimizer/"):
        candidates.append(relative[len("resume-optimizer/"):])
    for candidate in candidates:
        if candidate == "jobs/job.txt":
            continue
        if candidate in PRIVATE_EXACT_PATHS:
            return "private path is tracked or unignored"
        posix_path = PurePosixPath(candidate)
        for pattern in PRIVATE_PATH_GLOBS:
            if posix_path.match(pattern):
                return f"private path matches {pattern}"
    return None


def scan_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    findings: list[str] = []
    for name, pattern in SECRET_PATTERNS.items():
        for match in pattern.finditer(text):
            findings.append(f"{path}: {name}: {mask(match.group(0))}")
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan Git-tracked and unignored files for common secrets.")
    parser.add_argument("--fail-on-finding", action="store_true")
    parser.add_argument(
        "--check-history",
        action="store_true",
        help="Also fail when any reachable Git history contains a private path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings: list[str] = []
    for path in git_paths():
        if not path.exists():
            continue
        reason = private_path_reason(path)
        if reason:
            findings.append(f"{path}: private_path: {reason}")
        if path.is_file() and not should_skip(path):
            findings.extend(scan_file(path))
    if args.check_history:
        for path in history_paths():
            reason = private_path_reason(path)
            if reason:
                findings.append(f"{path}: history_private_path: {reason}")

    if findings:
        print("Potential secrets found:")
        for finding in findings:
            print(f"- {finding}")
        return 1 if args.fail_on_finding else 0

    print("No common secret patterns found in tracked or unignored files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
