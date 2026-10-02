#!/usr/bin/env python3
"""Initialize and validate inert Bipolix engineering-knowledge records."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
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



def dry_run_workflow(*, root: Path, sandbox: Path, subsystem: str) -> dict:
    """Read existing knowledge, then prove capture in an isolated synthetic tree.

    Only explicit knowledge documents are read. No Git subprocess, socket,
    ROS import, evidence ingestion, canonical write, or promotion is used.
    """
    root = root.resolve()
    sandbox = sandbox.resolve()
    repo = root.parents[1]
    if sandbox.is_relative_to(repo) or root.is_relative_to(sandbox):
        raise ValueError("sandbox must be outside the source repository and canonical tree")
    if sandbox.exists():
        raise ValueError("sandbox must be a new path; existing artifacts are never overwritten")
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", subsystem):
        raise ValueError("subsystem must be one uppercase taxonomy token")

    reads = []
    based_on_ids = []

    def read_document(path: Path, *, record: bool = False) -> str:
        if not path.resolve().is_relative_to(root):
            raise ValueError("knowledge source symlink escapes the explicit root")
        content = path.read_text(encoding="utf-8")
        data = _frontmatter(path) if record else {}
        reads.append({"path": str(path), "sha256": hashlib.sha256(content.encode()).hexdigest(),
                      "id": data.get("id", "SUMMARY")})
        return content

    policy_text = ""
    for name in ("README.md", "CAPABILITY_MATRIX.md", "KNOWN_GOOD_CONFIGURATIONS.md",
                 "KNOWN_BAD.md", "LESSONS_LEARNED.md"):
        content = read_document(root / name)
        if name == "README.md":
            policy_text = re.sub(r"\s+", " ", content)
    policy_rules = [sentence for sentence in re.split(r"(?<=[.!?])\s+", policy_text)
                    if "physical" in sentence.lower() and
                    any(word in sentence.lower() for word in ("never", "separate")) and
                    any(word in sentence.lower() for word in ("offline", "mock"))]
    if not policy_rules:
        raise ValueError("README lacks an explicit offline/mock versus physical evidence rule")
    for directory in (root / "tests", root / "findings"):
        for path in sorted(directory.glob("*.md")):
            if not path.resolve().is_relative_to(root):
                raise ValueError("knowledge source symlink escapes the explicit root")
            data = _frontmatter(path)
            categories = {x.strip() for x in data.get("categories", "").split(",")}
            if subsystem in categories:
                read_document(path, record=True)
                based_on_ids.append(data["id"])
    if not based_on_ids:
        raise ValueError("no relevant records; choose a documented subsystem before deciding")

    # The decision follows successful reads. Existing historical evidence cannot
    # turn this mock analysis into physical acceptance or an authorized command.
    decision = {"based_on_ids": based_on_ids, "physical_proof": False,
                "action": "INERT_ANALYSIS_ONLY", "reason": "This demonstration has no physical observation",
                "source_rule": policy_rules[0], "source_rule_document": str(root / "README.md")}
    analysis = {"physical_observation": False, "classification": "OFFLINE_PROVEN",
                "result": "PASS", "scope": "SYNTHETIC evidence-class separation only"}
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    day = now.split("T", 1)[0].replace("-", "")
    sandbox.mkdir(parents=True, exist_ok=False)
    for folder in ("tests", "findings"):
        (sandbox / folder).mkdir()
    test_id, finding_id = f"TEST-{day}-001", f"FINDING-{day}-001"
    test_path = sandbox / "tests" / f"{test_id}-synthetic-workflow.md"
    finding_path = sandbox / "findings" / f"{finding_id}-synthetic-evidence-boundary.md"
    test_path.write_text(f"""---
schema: bipolix.test_session/v1
id: {test_id}
title: SYNTHETIC offline knowledge workflow demonstration
date: {now.split('T', 1)[0]}
classification: OFFLINE_PROVEN
result: PASS
categories: {subsystem}
robot_id: SYNTHETIC_NO_ROBOT
git_sha: UNKNOWN
evidence: ../evidence.json
synthetic: true
review_status: SYNTHETIC_DRAFT
applicability: NONE
---

# SYNTHETIC — workflow proof, no physical acceptance

Objective: read relevant existing knowledge before an inert evidence-class decision.
Acceptance: no physical observation stays offline; source IDs were read first;
only this external sandbox changes; records and indexes validate.
FAIL: physical proof inferred, canonical content changed, or consistency invalid.
ABORT: any hardware, network, ROS, or secret-bearing evidence operation requested.
Actual: inert classification PASS, physical proof false; no robot commands sent.
This PASS covers the synthetic workflow only. Human review is required before
any real draft enters canonical knowledge. Related [finding](../findings/{finding_path.name}).
""", encoding="utf-8")
    finding_path.write_text(f"""---
schema: bipolix.engineering_finding/v1
id: {finding_id}
title: SYNTHETIC offline evidence does not establish physical acceptance
date: {now.split('T', 1)[0]}
status: HISTORICAL
categories: {subsystem}
evidence: ../evidence.json
synthetic: true
review_status: SYNTHETIC_DRAFT
applicability: NONE
---

# SYNTHETIC — demonstration only, not canonical engineering knowledge

Observation: relevant existing records were read before the mock decision.
Root cause/fix/retest: no real incident occurred; NOT APPLICABLE.
Lesson demonstrated: a mock result never creates physical proof or hardware permission.
Validation: [synthetic session](../tests/{test_path.name}); sandbox validator.
No robot/model/firmware/site applicability and no cross-robot propagation.
""", encoding="utf-8")
    (sandbox / "TEST_REGISTRY.md").write_text(
        f"# SYNTHETIC sandbox tests\n\n[{test_id}](tests/{test_path.name})\n", encoding="utf-8")
    (sandbox / "FINDING_REGISTRY.md").write_text(
        f"# SYNTHETIC sandbox findings\n\n[{finding_id}](findings/{finding_path.name})\n", encoding="utf-8")
    (sandbox / "README.md").write_text(
        "# SYNTHETIC offline workflow sandbox\n\nNever promote these demonstration records to canonical history.\n",
        encoding="utf-8")
    report = {"synthetic": True, "source_root": str(root), "sandbox": str(sandbox),
              "subsystem": subsystem, "read_before_decision": reads, "decision": decision,
              "inert_analysis": analysis, "hardware_commands_sent": 0,
              "stages": ["discover", "read", "decide", "inert_analysis", "draft", "index", "validate"]}
    (sandbox / "evidence.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report["validation_errors"] = validate_tree(sandbox)
    (sandbox / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


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
    dry_run = subparsers.add_parser("dry-run", help="SYNTHETIC workflow proof outside canonical knowledge")
    dry_run.add_argument("--root", type=Path, default=_default_root())
    dry_run.add_argument("--sandbox", type=Path, required=True)
    dry_run.add_argument("--subsystem", required=True)
    args = parser.parse_args(argv)
    if args.command == "dry-run":
        try:
            report = dry_run_workflow(root=args.root, sandbox=args.sandbox, subsystem=args.subsystem)
        except (ValueError, OSError) as error:
            parser.error(str(error))
        print(json.dumps(report, indent=2))
        return 1 if report["validation_errors"] else 0
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
