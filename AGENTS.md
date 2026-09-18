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
- A build/test pass proves software behavior only, never hardware safety.
- Before handoff, review the diff and report branch, full SHA, tests, hardware
  commands sent, evidence limitations, and the next safe action.
