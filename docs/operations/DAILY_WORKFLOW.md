# Daily engineering workflow

Use this workflow for product, architecture and physical-test work. Scope and
evidence may be small, but no step is silently skipped.

## Start of day

1. Read `docs/architecture/ARCHITECTURE.md` and affected ADRs.
2. Read the current-state/known-good handoff and repository status.
3. Define one concrete objective and explicit non-goals.
4. Identify the affected architectural layer and authoritative owner.
5. Identify safety impact, ownership path and whether hardware could move.
6. Define focused tests and, for physical work, PASS/FAIL/ABORT before changes.

## Development

7. Implement offline through existing contracts; avoid duplicate runtimes,
   controllers, publishers and safety paths.
8. Run focused tests and `git diff --check`.
9. Run simulation/replay when applicable and label that evidence accurately.

## Physical validation

10. Perform a read-only preflight of posture, health, source, data freshness,
    environment, limits, stop path and evidence capture.
11. Obtain explicit approval for the exact motion and run one controlled
    experiment using `docs/testing/EXPERIMENT_TEMPLATE.md`.
12. Capture results, diagnostics and terminal cleanup; interrupted evidence is
    not a PASS.

## End of day

13. Run focused regression and the relevant full suite.
14. Update source-of-truth documentation, requirement/test status and known
    issues without overstating evidence.
15. Review status/diff for secrets, generated output and unrelated changes.
16. Create a logical commit; push only to the verified remote with permission.
17. Update current state and the known-good baseline only after its gates pass.
18. Record exactly one recommended next safe step and its prerequisites.

