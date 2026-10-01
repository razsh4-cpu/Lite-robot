# Codex working agreement

These rules apply repository-wide. Nested `AGENTS.md` files may add local build
instructions but may never weaken these safety or Git requirements.

## Git and evidence

- Start from recorded `git status --short --branch` and `git rev-parse HEAD`.
- Work on a dedicated milestone branch; never merge, reset, force-push, rewrite
  shared history, or overwrite local work without explicit approval.
- Treat only committed evidence as committed evidence. Hardware reports, videos,
  local `/tmp` files, replay, and simulation are distinct evidence classes.
- Keep generated builds, logs, credentials, and host-specific data out of Git.

## Robot safety

- Default to offline analysis, inert transports, simulation, and tests.
- Never run a hardware-facing executable, request ownership, enable a send gate,
  transmit a robot command, or repeat a physical test without approval of that
  exact run after review of limits, preflight, abort behavior, and evidence plan.
- Never weaken a guard, permit, timeout, interlock, release path, or operator
  requirement to make a test pass. No raw torque, RL, gait velocity, Nav2, or
  autonomous movement during low-level body-shift milestones.
- Keep milestones ordered: supported stand, body shift, unloading, then leg lift.

## Validation and handoff

- Run focused offline tests, the relevant full suite, and `git diff --check`.
- Follow `docs/operations/DAILY_WORKFLOW.md`, the project-wide Definition of
  Done, and the maintained test catalog; define PASS/FAIL/ABORT before a
  physical experiment.
- A build/test pass proves software behavior only, never hardware safety.
- Before handoff, review the diff and report branch, full SHA, tests, hardware
  commands sent, evidence limitations, and the next safe action.

## Architecture source of truth

- Before changing product architecture, read
  `docs/architecture/ARCHITECTURE.md` and
  `docs/architecture/ROBOT_PLATFORM.md`.
- Preserve the dependency direction and the single-owner runtime boundaries
  documented there. Update the architecture record when an approved change
  alters those boundaries.

## Engineering knowledge workflow

- `docs/engineering/README.md` is the canonical knowledge entry point. Before
  modifying or testing a subsystem, read its Capability Matrix row, relevant
  Engineering Findings, and relevant prior Test Sessions.
- Before a meaningful experiment, create a `bipolix.test_session/v1` record and
  define objective, evidence, PASS/FAIL/ABORT, and safety boundaries. A record
  never authorizes hardware action.
- After meaningful testing or debugging, close the Test Session and create or
  update a `bipolix.engineering_finding/v1` record when reusable knowledge was
  learned. Preserve failures and partial results even after a later pass.
- Never promote offline/mock work to physical proof or invent missing history;
  use `UNKNOWN`, `HISTORICAL_CLAIM`, `INCONCLUSIVE`, or `EVIDENCE MISSING`.
- Update the Capability Matrix only when evidence justifies the change, keep
  primary artifacts in their authoritative location, and run
  `python3 tools/engineering_knowledge.py validate` before handoff.
