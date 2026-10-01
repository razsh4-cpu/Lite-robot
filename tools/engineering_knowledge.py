#!/usr/bin/env python3
"""Initialize and validate inert Bipolix engineering-knowledge records."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import socket
import subprocess
import sys
from pathlib import Path


TEST_CLASSIFICATIONS = {
    "PHYSICALLY_PROVEN",
    "LIVE_STATIC_PROVEN",
    "OFFLINE_PROVEN",
    "FAILED",
    "PARTIAL",
    "INCONCLUSIVE",
    "PLANNED",
    "HISTORICAL_CLAIM",
    "SUPERSEDED",
}
TEST_RESULTS = {"PASS", "FAIL", "PARTIAL", "INCONCLUSIVE", "PLANNED", "UNKNOWN"}
FINDING_STATUSES = {
    "CURRENT",
    "KNOWN_ISSUE",
    "HISTORICAL",
    "SUPERSEDED",
    "DO_NOT_USE",
    "RESOLVED",
}
SCHEMAS = {"bipolix.test_session/v1", "bipolix.engineering_finding/v1"}
LINK_RE = re.compile(r"(?<!!)\[[^]]*]\(([^)]+)\)")


def _slug(title: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return value[:64] or "record"


def next_id(root: Path, kind: str, day: str) -> str:
    prefix = "TEST" if kind == "test" else "FINDING"
    directory = root / ("tests" if kind == "test" else "findings")
    numbers = []
    for path in directory.glob(f"{prefix}-{day}-*.md"):
        match = re.match(rf"{prefix}-{day}-(\d{{3}})(?:-|\.md)", path.name)
        if match:
            numbers.append(int(match.group(1)))
    return f"{prefix}-{day}-{max(numbers, default=0) + 1:03d}"


def _git_value(repo: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
        return result.stdout.strip() or "UNKNOWN"
    except (OSError, subprocess.SubprocessError):
        return "UNKNOWN"


def render_test_session(
    *,
    record_id: str,
    title: str,
    timestamp: str,
    hostname: str,
    robot_id: str,
    repository: str,
    branch: str,
    git_sha: str,
    git_state: str,
) -> str:
    date = timestamp.split("T", 1)[0]
    return f"""---
schema: bipolix.test_session/v1
id: {record_id}
title: {title}
date: {date}
classification: PLANNED
result: PLANNED
actual_behavior: UNKNOWN
categories: UNKNOWN
robot_id: {robot_id}
git_sha: {git_sha}
evidence: EVIDENCE MISSING
---

# {record_id} — {title}

## Provenance

- Timestamp: `{timestamp}`
- Hostname: `{hostname}`
- Repository: `{repository}`
- Branch: `{branch}`
- Git state: `{git_state}`
- Hardware configuration: `UNKNOWN`
- Site / map: `UNKNOWN`
- Operator: `UNKNOWN`

## Objective and acceptance

- Objective: `TODO`
- Preconditions: `TODO`
- Acceptance criteria: `TODO`
- Safety boundaries: `TODO`

## Procedure and result

- Procedure: `TODO`
- Expected behavior: `TODO`
- Actual behavior: `UNKNOWN`
- Metrics: `UNKNOWN`
- Failure reason: `UNKNOWN`
- Safety events: `UNKNOWN`

## Evidence and follow-up

- Logs / rosbag / video / images: `EVIDENCE MISSING`
- Related commits / issues / findings: `UNKNOWN`
- Lessons learned: `UNKNOWN`
- Follow-up: `UNKNOWN`
- Supersedes / superseded by: `UNKNOWN`
"""


def render_finding(
    *,
    record_id: str,
    title: str,
    timestamp: str,
    hostname: str,
    repository: str,
    branch: str,
    git_sha: str,
    git_state: str,
) -> str:
    date = timestamp.split("T", 1)[0]
    return f"""---
schema: bipolix.engineering_finding/v1
id: {record_id}
title: {title}
date: {date}
status: CURRENT
categories: UNKNOWN
evidence: EVIDENCE MISSING
---

# {record_id} — {title}

## Provenance

- Timestamp: `{timestamp}`
- Hostname: `{hostname}`
- Repository: `{repository}`
- Branch: `{branch}`
- Git SHA: `{git_sha}`
- Git state: `{git_state}`

## Finding

- Context: `TODO`
- Observation: `TODO`
- Expected behavior: `TODO`
- Actual behavior: `TODO`
- Root cause: `UNKNOWN`
- Fix / workaround: `UNKNOWN`
- Validation: `UNKNOWN`
- Known-good configuration: `UNKNOWN`
- Known-bad configuration: `UNKNOWN`
- DO NOT REPEAT: `UNKNOWN`

## Evidence and relationships

- Primary evidence: `EVIDENCE MISSING`
- Affected versions / SHAs: `UNKNOWN`
- Related tests / findings / commits: `UNKNOWN`
- Supersedes / superseded by: `UNKNOWN`
- Lessons learned: `UNKNOWN`
"""


def initialize_record(
    *,
    root: Path,
    kind: str,
    title: str,
    robot_id: str = "UNKNOWN",
    now: str | None = None,
    hostname: str | None = None,
    repo: Path | None = None,
) -> Path:
    if kind not in {"test", "finding"}:
        raise ValueError("kind must be test or finding")
    root = root.resolve()
    repo = (repo or Path.cwd()).resolve()
    timestamp = now or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    day = timestamp.split("T", 1)[0].replace("-", "")
    record_id = next_id(root, kind, day)
    directory = root / ("tests" if kind == "test" else "findings")
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"{record_id}-{_slug(title)}.md"
    branch = _git_value(repo, "branch", "--show-current")
    sha = _git_value(repo, "rev-parse", "HEAD")
    dirty = _git_value(repo, "status", "--porcelain")
    state = "CLEAN" if dirty in {"", "UNKNOWN"} else "DIRTY"
    common = dict(
        record_id=record_id,
        title=title,
        timestamp=timestamp,
        hostname=hostname or socket.gethostname(),
        repository=repo.name,
        branch=branch,
        git_sha=sha,
        git_state=state,
    )
    content = (
        render_test_session(robot_id=robot_id, **common)
        if kind == "test"
        else render_finding(**common)
    )
    destination.write_text(content, encoding="utf-8")
    return destination


def _frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return result
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return {}


def _validate_links(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for raw in LINK_RE.findall(text):
            target = raw.split("#", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"{path}: broken local link {raw}")
    return errors


def validate_tree(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    seen: dict[str, Path] = {}
    test_registry = (root / "TEST_REGISTRY.md").read_text(encoding="utf-8") if (root / "TEST_REGISTRY.md").exists() else ""
    finding_registry = (root / "FINDING_REGISTRY.md").read_text(encoding="utf-8") if (root / "FINDING_REGISTRY.md").exists() else ""
    for kind, directory in (("test", root / "tests"), ("finding", root / "findings")):
        for path in sorted(directory.glob("*.md")):
            data = _frontmatter(path)
            required = (
                {"schema", "id", "title", "date", "classification", "result", "categories", "robot_id", "git_sha", "evidence"}
                if kind == "test"
                else {"schema", "id", "title", "date", "status", "categories", "evidence"}
            )
            missing = sorted(required - data.keys())
            if missing:
                errors.append(f"{path}: missing metadata {', '.join(missing)}")
                continue
            record_id = data["id"]
            if record_id in seen:
                errors.append(f"{path}: duplicate id {record_id} also in {seen[record_id]}")
            seen[record_id] = path
            if not path.name.startswith(record_id):
                errors.append(f"{path}: filename does not start with id {record_id}")
            if data["schema"] not in SCHEMAS:
                errors.append(f"{path}: invalid schema {data['schema']}")
            registry = test_registry if kind == "test" else finding_registry
            registry_name = "TEST_REGISTRY.md" if kind == "test" else "FINDING_REGISTRY.md"
            if record_id not in registry:
                errors.append(f"{path}: {record_id} missing from {registry_name}")
            if kind == "test":
                if data["classification"] not in TEST_CLASSIFICATIONS:
                    errors.append(f"{path}: invalid test classification {data['classification']}")
                if data["result"] not in TEST_RESULTS:
                    errors.append(f"{path}: invalid test result {data['result']}")
                if data["classification"] == "PLANNED" and data["result"] != "PLANNED":
                    errors.append(f"{path}: PLANNED record must use result PLANNED")
            elif data["status"] not in FINDING_STATUSES:
                errors.append(f"{path}: invalid finding status {data['status']}")
    errors.extend(_validate_links(root))
    return errors


def _default_root() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "engineering"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command, kind in (("new-test", "test"), ("new-finding", "finding")):
        child = subparsers.add_parser(command)
        child.set_defaults(kind=kind)
        child.add_argument("--title", required=True)
        child.add_argument("--robot-id", default="UNKNOWN")
        child.add_argument("--root", type=Path, default=_default_root())
        child.add_argument("--repo", type=Path, default=Path.cwd())
    validate = subparsers.add_parser("validate")
    validate.add_argument("--root", type=Path, default=_default_root())
    args = parser.parse_args(argv)
    if args.command == "validate":
        errors = validate_tree(args.root)
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print(f"Engineering knowledge validation passed: {args.root}")
        return 0
    path = initialize_record(
        root=args.root,
        kind=args.kind,
        title=args.title,
        robot_id=args.robot_id,
        repo=args.repo,
    )
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
