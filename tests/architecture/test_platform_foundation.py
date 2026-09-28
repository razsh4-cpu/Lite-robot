from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]


def text(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase_one_foundation_documents_exist():
    required = (
        "docs/architecture/decisions/ADR-005-motion-through-existing-safety-path.md",
        "docs/requirements/MVP_REQUIREMENTS.md",
        "docs/requirements/ODD.md",
        "docs/testing/DEFINITION_OF_DONE.md",
        "docs/testing/TEST_CATALOG.md",
        "docs/testing/EXPERIMENT_TEMPLATE.md",
        "docs/testing/BLACK_BOX_DESIGN.md",
        "docs/testing/KNOWN_GOOD_BASELINE.md",
        "docs/operations/ENGINEERING_KNOWLEDGE_BASE.md",
        "docs/operations/FAILURE_MATRIX.md",
        "docs/operations/PERFORMANCE_BASELINE.md",
        "docs/operations/FUTURE_ENGINEERING_FOUNDATIONS.md",
        "docs/operations/DAILY_WORKFLOW.md",
    )
    for path in required:
        assert (ROOT / path).is_file(), path


def test_requirements_use_only_allowed_evidence_statuses():
    body = text("docs/requirements/MVP_REQUIREMENTS.md")
    statuses = set(re.findall(r"\| (PROVEN|PARTIAL|PLANNED) \|", body))
    assert statuses == {"PROVEN", "PARTIAL", "PLANNED"}
    assert "chair" in body.lower()
    assert "COMMAND_SOURCE=NONE" in body


def test_definition_of_done_keeps_physical_evidence_distinct():
    body = text("docs/testing/DEFINITION_OF_DONE.md")
    for stage in (
        "DESIGNED", "IMPLEMENTED", "OFFLINE TESTED", "SIMULATION TESTED",
        "PHYSICALLY VALIDATED", "REGRESSION TESTED", "DOCUMENTED", "RELEASED",
    ):
        assert stage in body
    assert "does not" in body.lower() and "hardware" in body.lower()


def test_catalog_has_expected_ids_and_experiment_abort_contract():
    catalog = text("docs/testing/TEST_CATALOG.md")
    for number in range(1, 16):
        assert f"T{number:03d}" in catalog
    template = text("docs/testing/EXPERIMENT_TEMPLATE.md")
    for heading in (
        "QUESTION", "HYPOTHESIS", "SETUP", "PRECONDITIONS", "PASS",
        "FAIL", "ABORT", "DATA TO RECORD", "RESULT", "CONCLUSION",
    ):
        assert heading in template


def test_failure_matrix_does_not_overclaim_every_recovery():
    body = text("docs/operations/FAILURE_MATRIX.md")
    for status in ("IMPLEMENTED", "PARTIAL", "PLANNED"):
        assert status in body
    assert "300 ms" in body
    assert "COMMAND_SOURCE=NONE" in body


def test_performance_baseline_records_measured_before_and_after():
    body = text("docs/operations/PERFORMANCE_BASELINE.md")
    for evidence in (
        "9.02 / 7.69 / 5.11", "1.7 GiB", "98%",
        "1.33 / 1.08 / 0.56", "1.0 GiB", "0%",
    ):
        assert evidence in body
    assert "Do not optimize further" in body


def test_known_good_baseline_preserves_terminal_safety_evidence():
    body = text("docs/testing/KNOWN_GOOD_BASELINE.md")
    for evidence in (
        "1.47 m", "NavigateToPose", "COMMAND_SOURCE=NONE", "PHYSICALLY PROVEN",
    ):
        assert evidence in body


def test_black_box_design_is_observational_not_a_motion_path():
    body = text("docs/testing/BLACK_BOX_DESIGN.md")
    assert "test start <experiment_name>" in body
    assert "test stop" in body
    assert "must never acquire" in body
    assert "must never publish" in body


def test_foundation_introduces_no_runtime_unit_or_launch():
    names = ("platform-foundation", "black-box", "known-good-baseline")
    for name in names:
        assert not list(ROOT.glob(f"**/*{name}*.service"))
        assert not list(ROOT.glob(f"**/*{name}*.launch.py"))


def test_architecture_links_to_phase_one_foundation():
    body = text("docs/architecture/ARCHITECTURE.md")
    for link in (
        "../requirements/MVP_REQUIREMENTS.md",
        "../requirements/ODD.md",
        "../testing/DEFINITION_OF_DONE.md",
        "../testing/TEST_CATALOG.md",
        "../testing/KNOWN_GOOD_BASELINE.md",
        "../operations/FAILURE_MATRIX.md",
        "../operations/ENGINEERING_KNOWLEDGE_BASE.md",
        "decisions/ADR-005-motion-through-existing-safety-path.md",
    ):
        assert link in body
