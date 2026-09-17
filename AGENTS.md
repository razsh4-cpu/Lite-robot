# Codex working agreement

These instructions apply to the entire repository. A more deeply nested
`AGENTS.md` or `AGENTS.override.md`, if one is added later, may refine local
build or test details but must not weaken the safety and Git rules below.

## Start every task from known Git state

1. Run `git fetch --all --prune`.
2. Record `git status --short --branch` and `git rev-parse HEAD` before editing.
3. Read the current status, safety, experiment, and handoff documents relevant
   to the requested milestone. Do not treat a video, chat report, local file,
   uncommitted result, or offline replay as committed hardware evidence.
4. Work on a dedicated branch for one milestone. Do not work directly on
   `main` or a shared research branch. Do not merge, force-push, rewrite shared
   history, delete remote branches, or push unrelated local changes.

## Work and validation

- Keep milestones separate. Do not begin a later milestone because an earlier
  one looks promising.
- Prefer offline analysis, inert transports, simulations, and focused tests.
- Never run a hardware-facing executable, send a robot command, connect to or
  deploy onto the robot, or repeat a hardware experiment unless the user has
  explicitly approved that exact run after reviewing its current preflight,
  limits, abort behavior, and evidence plan.
- Never weaken or bypass a safety gate, permit, interlock, telemetry check,
  ownership check, timeout, abort path, release rule, or operator requirement.
- Do not add secrets, credentials, tokens, private keys, host-specific auth
  data, generated build trees, or unrelated logs to Git.
- Run the smallest relevant offline test set before calling work complete.
  Also run `git diff --check`. Record exact commands and results. A build or
  test pass is not proof of hardware behavior.
- If tests fail or required evidence is missing, do not describe the milestone
  as complete. Keep the branch clearly marked blocked or incomplete and do not
  blindly push a misleading success state.

## End every task with a Git handoff

1. Review the diff and repository status. Ensure only milestone files are
   included.
2. Commit the coherent result on the dedicated branch with a specific message.
3. Push the branch when the commit is safe to share. Never push secrets,
   unrelated changes, or a commit that falsely claims success. If a blocked or
   failing state must be shared, label it clearly as `WIP` or `BLOCKED` in the
   commit and handoff and include the exact failures.
4. Do not merge. Leave review and merge decisions to the user.
5. Finish with this handoff, using a full 40-character commit SHA:

```text
STATUS: READY_FOR_REVIEW | BLOCKED | EVIDENCE_INCOMPLETE
BRANCH: <branch>
COMMIT: <full SHA>
CHANGES:
- <what changed>
TESTS:
- <exact command> -> <PASS/FAIL/NOT RUN and reason>
HARDWARE:
- Commands sent: NONE | <exact approved run and result>
- Hardware state/final posture: <observed fact or UNKNOWN>
EVIDENCE:
- <committed paths and what each proves>
MISSING:
- <missing proof, parameters, access, or decisions>
NEXT SAFE ACTION:
- <one bounded action; default to offline work or review>
```

A handoff is incomplete without the branch, full SHA, test results, hardware
statement, evidence limits, and next safe action.
