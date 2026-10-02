from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "engineering_knowledge", ROOT / "tools" / "engineering_knowledge.py"
)
assert SPEC and SPEC.loader
knowledge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(knowledge)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_next_id_is_deterministic_and_separate_by_record_type(tmp_path: Path) -> None:
    write(tmp_path / "tests" / "TEST-20261001-001-first.md", "")
    write(tmp_path / "tests" / "TEST-20261001-003-third.md", "")
    write(tmp_path / "findings" / "FINDING-20261001-001-first.md", "")

    assert knowledge.next_id(tmp_path, "test", "20261001") == "TEST-20261001-004"
    assert knowledge.next_id(tmp_path, "finding", "20261001") == "FINDING-20261001-002"


def test_test_initializer_is_planned_and_does_not_claim_execution(tmp_path: Path) -> None:
    rendered = knowledge.render_test_session(
        record_id="TEST-20261001-001",
        title="Bounded Xbox forward and stop",
        timestamp="2026-10-01T10:00:00+03:00",
        hostname="laptop",
        robot_id="robodog_01",
        repository="Lite-robot",
        branch="feature/test",
        git_sha="abc123",
        git_state="DIRTY",
    )

    assert "schema: bipolix.test_session/v1" in rendered
    assert "classification: PLANNED" in rendered
    assert "result: PLANNED" in rendered
    assert "actual_behavior: UNKNOWN" in rendered
    assert "PHYSICALLY_PROVEN" not in rendered
    assert "robot commands" not in rendered.lower()


def test_validator_rejects_planned_session_that_claims_pass(tmp_path: Path) -> None:
    write(
        tmp_path / "tests" / "TEST-20261001-001-bad.md",
        """---
schema: bipolix.test_session/v1
id: TEST-20261001-001
title: Bad planned record
date: 2026-10-01
classification: PLANNED
result: PASS
categories: SAFETY
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: EVIDENCE MISSING
---
""",
    )
    write(tmp_path / "TEST_REGISTRY.md", "TEST-20261001-001\n")
    write(tmp_path / "FINDING_REGISTRY.md", "# Findings\n")

    errors = knowledge.validate_tree(tmp_path)

    assert any("PLANNED record must use result PLANNED" in error for error in errors)


def test_validator_rejects_invalid_controlled_values_and_unregistered_record(
    tmp_path: Path,
) -> None:
    write(
        tmp_path / "findings" / "FINDING-20261001-001-bad.md",
        """---
schema: bipolix.engineering_finding/v1
id: FINDING-20261001-001
title: Bad status
date: 2026-10-01
status: MAYBE
categories: NETWORKING
evidence: EVIDENCE MISSING
---
""",
    )
    write(tmp_path / "TEST_REGISTRY.md", "# Tests\n")
    write(tmp_path / "FINDING_REGISTRY.md", "# Findings\n")

    errors = knowledge.validate_tree(tmp_path)

    assert any("invalid finding status MAYBE" in error for error in errors)
    assert any("missing from FINDING_REGISTRY.md" in error for error in errors)


def test_validator_accepts_missing_historical_evidence_marker(tmp_path: Path) -> None:
    record = tmp_path / "tests" / "TEST-20261001-001-history.md"
    write(
        record,
        """---
schema: bipolix.test_session/v1
id: TEST-20261001-001
title: Historical claim
date: UNKNOWN
classification: HISTORICAL_CLAIM
result: INCONCLUSIVE
categories: ROBOT_CONTROL
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: EVIDENCE MISSING
---
""",
    )
    write(tmp_path / "TEST_REGISTRY.md", "[TEST-20261001-001](tests/TEST-20261001-001-history.md)\n")
    write(tmp_path / "FINDING_REGISTRY.md", "# Findings\n")

    assert knowledge.validate_tree(tmp_path) == []


def test_validator_reports_broken_local_markdown_link(tmp_path: Path) -> None:
    write(tmp_path / "README.md", "[missing](findings/nope.md)\n")
    write(tmp_path / "TEST_REGISTRY.md", "# Tests\n")
    write(tmp_path / "FINDING_REGISTRY.md", "# Findings\n")

    errors = knowledge.validate_tree(tmp_path)

    assert any("broken local link" in error for error in errors)


@pytest.mark.parametrize("kind", ["test", "finding"])
def test_initializer_writes_only_below_requested_root(tmp_path: Path, kind: str) -> None:
    path = knowledge.initialize_record(
        root=tmp_path / "engineering",
        kind=kind,
        title="Safe initializer",
        robot_id="robot_01",
        now="2026-10-01T10:00:00+03:00",
        hostname="offline-host",
        repo=tmp_path,
    )

    assert path.is_relative_to(tmp_path / "engineering")
    assert path.exists()
    assert not list(tmp_path.glob("owner.lock"))


def demo_source(tmp_path: Path) -> Path:
    source = tmp_path / "repo" / "docs" / "engineering"
    for name in ["README.md", "CAPABILITY_MATRIX.md", "KNOWN_GOOD_CONFIGURATIONS.md", "KNOWN_BAD.md", "LESSONS_LEARNED.md"]:
        write(source / name, f"# {name}\nKeep offline evidence separate from physical acceptance.\n")
    write(source / "findings" / "FINDING-20261001-001-source.md", """---
schema: bipolix.engineering_finding/v1
id: FINDING-20261001-001
title: Source evidence boundary
date: 2026-10-01
status: CURRENT
categories: SAFETY
evidence: EVIDENCE MISSING
---
Offline evidence cannot authorize hardware.
""")
    return source


def test_dry_run_reads_before_decision_and_validates_synthetic_sandbox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = demo_source(tmp_path)
    before = {p.relative_to(source): p.read_bytes() for p in source.rglob("*") if p.is_file()}

    def forbidden(*args, **kwargs):
        raise AssertionError("dry-run must not use sockets or subprocesses")

    monkeypatch.setattr(knowledge.socket, "socket", forbidden)
    monkeypatch.setattr(knowledge.subprocess, "run", forbidden)
    sandbox = tmp_path / "sandbox"
    report = knowledge.dry_run_workflow(root=source, sandbox=sandbox, subsystem="SAFETY")

    assert report["stages"] == ["discover", "read", "decide", "inert_analysis", "draft", "index", "validate"]
    assert report["decision"]["physical_proof"] is False
    assert "offline evidence" in report["decision"]["source_rule"].lower()
    assert report["decision"]["source_rule_document"] == str(source / "README.md")
    assert report["decision"]["based_on_ids"] == ["FINDING-20261001-001"]
    assert report["validation_errors"] == []
    assert report["synthetic"] is True
    assert report["hardware_commands_sent"] == 0
    assert knowledge.validate_tree(sandbox) == []
    assert before == {p.relative_to(source): p.read_bytes() for p in source.rglob("*") if p.is_file()}
    for path in list((sandbox / "tests").glob("*.md")) + list((sandbox / "findings").glob("*.md")):
        assert "SYNTHETIC" in path.read_text()
        assert "PHYSICALLY_PROVEN" not in path.read_text()
    assert list((sandbox / "tests").glob("*.md"))
    assert list((sandbox / "findings").glob("*.md"))


@pytest.mark.parametrize("destination", ["canonical", "under_repo", "nonempty"])
def test_dry_run_refuses_canonical_or_existing_destinations(tmp_path: Path, destination: str) -> None:
    source = demo_source(tmp_path)
    sandbox = source if destination == "canonical" else source.parents[1] / "scratch" if destination == "under_repo" else tmp_path / "nonempty"
    if destination == "nonempty":
        write(sandbox / "existing.txt", "keep")
    with pytest.raises(ValueError):
        knowledge.dry_run_workflow(root=source, sandbox=sandbox, subsystem="SAFETY")
    if destination == "nonempty":
        assert (sandbox / "existing.txt").read_text() == "keep"


def test_dry_run_missing_knowledge_fails_without_creating_records(tmp_path: Path) -> None:
    source = demo_source(tmp_path)
    sandbox = tmp_path / "sandbox"
    with pytest.raises(ValueError, match="relevant"):
        knowledge.dry_run_workflow(root=source, sandbox=sandbox, subsystem="DOES_NOT_EXIST")
    assert not sandbox.exists()
