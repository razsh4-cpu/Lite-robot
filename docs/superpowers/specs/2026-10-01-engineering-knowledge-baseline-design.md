# Bipolix engineering knowledge baseline design

## Purpose

Make `docs/engineering/` the canonical entry point for durable engineering
knowledge without replacing the existing authoritative architecture, test,
operations, handoff, R&D, or artifact locations.

## Records

The baseline uses two small, reviewable Markdown record types:

- `bipolix.test_session/v1` for an explicit experiment or validation;
- `bipolix.engineering_finding/v1` for reusable debugging, integration,
  deployment, architecture, or reliability knowledge.

Each record carries controlled classification/status fields and links to
primary evidence. Unknown historical fields remain `UNKNOWN`; missing evidence
is written as `EVIDENCE MISSING`. A later success never deletes an earlier
failure.

## Canonical layout

```text
docs/engineering/
├── README.md
├── CAPABILITY_MATRIX.md
├── CURRENT_STATE.md
├── KNOWN_ISSUES.md
├── KNOWN_BAD.md
├── LESSONS_LEARNED.md
├── TEST_REGISTRY.md
├── FINDING_REGISTRY.md
├── tests/
├── findings/
└── templates/
```

Large evidence remains at its existing authoritative path. The registry links
to it instead of duplicating or moving it.

## Lightweight tooling

`tools/engineering_knowledge.py` provides:

- inert initialization of a test-session or finding record;
- safe collection of timestamp, hostname, repository, Git SHA, branch, and
  dirty/clean state;
- consistency validation for schemas, IDs, controlled values, duplicate IDs,
  planned-test claims, registry membership, and local Markdown links.

The tool performs no ROS, networking, ownership, configuration, or robot
operations.

## Workflow

Before subsystem work, consult the capability matrix, relevant findings, and
prior sessions. Create a test record before meaningful experiments and finish
it afterward. Create/update a finding only when work yields reusable knowledge.
Update the capability matrix only when evidence justifies a maturity change.

## Safety and scope

This baseline changes documentation and offline tooling only. It does not
change runtime behavior, safety semantics, deployment, or hardware state.
