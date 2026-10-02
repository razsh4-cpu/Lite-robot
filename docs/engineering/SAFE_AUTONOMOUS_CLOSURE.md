# LITE3 / SABLE KNOWLEDGE & INTEGRATION CLOSURE COMPLETE

Safe source/offline closure, 2026-10-02. Deployment and physical validation remain separate human-supervised work. Initial read-only audit counts and deployed observations remain dated evidence; subsequent source reconciliation does not rewrite them.

1. **Historical sources inspected:** today's complete structured baseline; older registry records recovered from173f61d; current/historical Git, experiments/handoffs/validation reports, retained simulation tables; three operator-supplied historical Lite3 PDFs; targeted read-only Mini-PC source/install/service/config/bag/map metadata. See HISTORICAL_MASTER_INVENTORY and MINIPC_DEPLOYED_STATE_AUDIT for provenance.
2. **Mini-PC state:** deployed SABLE b4f6a48, editable ROS package resolution matched its tracked blobs; old Lite dirty checkout/symlink workspaces retained. Current deployed owner predates new authority/manual-start/battery guards. CPU J6413 lacks AVX. Domain23 SABLE versus legacy domain0 exporter must not be conflated. Protected broker config/raw unrestricted runtime text was not exported.
3. **Meaningful historical events:**92 independent scopes, two aliases (94 inventory entries), not94 independent experiments. No extra executions inferred from record reconstruction or plans.
4. **Test Sessions:**87 total after continuation, including five additional PLANNED stage records107–111. Historical/source closure before those plans82; existing baseline also contains planned records. Record count is not experiment count.
5. **Engineering Findings:**54.
6. **New reconstruction:** initial11tests/11findings→restored12tests/10findings→initial audit56tests/43findings→additional source-bounded25tests/10findings→one actual offline session/finding82/54→five PLANNED records87/54. Manifest ADDITIONAL_HISTORICAL_CAPTURE_20261002.json preserves source mapping; capture-date records do not invent run date/SHA.
7. **EVIDENCE_INCOMPLETE:**48 raw inventory scopes retain incomplete primary execution evidence. Completing record representation does not close missing proof.
8. **Historical gaps:** all92 scopes now represented by relevant Test/Finding kinds, but execution transcripts/configurations/robot IDs/raw payloads remain missing in many. Sep1–7 has no independently established dated event;131 keyword session artifacts are leads, not fully adjudicated experiments. Five bag payloads absent; two retained MCAP payloads were inspected only by metadata, not replayed. Secret/protected sources skipped.
9. **Known Good:** exact historical HIGH-LEVEL path forward/backward/yaw/curve and safe neutral/RB/shutdown behavior; configuration-bounded posture tests; Nav2 chair avoidance later accepted after an interrupted run; fresh correct map/TF/localization gates. Historical normalized x±.10→9174/−9175 and yaw±.25→−13107/+13106 are evidence for that path only.
10. **Known Bad / DO NOT REPEAT:** treat state98 as standing; infer lateral PASS from0x0131 existence; bypass ownership/watchdog; retain stale intent after reconnect; mix LOCAL_XBOX and laptop evidence; assume deployed/source identity; promote site speed/sign overrides; collapse interrupted/failing tests into later PASS; combine low-level supported R&D with product gait; assume null-guess ICP/incorrect TF/odom flooding is acceptable; power/charging experiments without hardware safety acceptance.
11. **Failure→fix→retest lessons:** ICP baseline correspondence rejection/null guess→candidate threshold replay (offline, not new physical proof); wrong TF→documented correction→later localization evidence; odom flooding reported~154Hz→throttle/config investigation (separate~200Hz bag metadata); chair run interruption→later accepted chair run; authorization expiry→bounded stand gate revisions→configuration-bounded later tests; Lease Ghost/stale owner→explicit ownership/recovery guards→static/offline validation; MPPI SIGILL on non-AVX→deployed RPP fallback→current offline source regression; idle standing odom drift→deployed dispatch freshness guard→current offline port. Full sequences and incomplete retests remain in individual records, not merged into PASS.
12. **Reconciliation matrix:** below. Complete nine-column capability comparison and full command paths remain in SABLE docs/LITE3_INTEGRATION.md; primary historical experiments/lessons in docs/LITE3_HISTORY_AUDIT.md and inventory.
13. **Incorporated:** single protected laptop teleop path, posture confirmation/neutral/new RB/continuous deadman, bounded lease/freshness/stop gates, configurable idle hold, CPU-compatible navigation choice, observable SI→normalized→encoded trace, narrowly forwarded existing driver readiness, UI UNKNOWN/refusal evidence, passive preparation and future knowledge workflow.
14. **Excluded:** second vendor writer/stack, Mini-PC-local Xbox requirement, hardcoded historical normalized calibration, unvalidated lateral claims, low-level R&D as product code, deployed site caps/sign as defaults, global state ownership and arbitrary service copying. These conflict with product architecture or lack applicable proof.
15. **Deployed fixes reconciled:** CPU fallback and idle odom concept reimplemented in existing navigation stack/driver, not copied wholesale. They are source/offline validated only; physical/navigation compatibility remains untested.
16. **Unresolved drift:** deployed b4 lacks new guards/diagnostics; site caps2/1.5/2 versus source.5/.3/.6, sign+,+,+ versus source−,+,+ for odom, calibration rationale UNKNOWN. Legacy exporter readiness/lateral claims stale. Build/run content-tree markers are not fullGitSHA; clock provenance uncertain. No deployment made.
17. **Capabilities:** current code support is not physical proof. Direct strafe UNVALIDATED; prior SABLE attempt FAILED_PHYSICAL with root cause UNKNOWN. Historical Raz ROS product forced linear.y0, so it supplies no direct lateral PASS. Current scaling/rate/gates/encoding/config differences require exact-path retest even for historically proven forward/yaw/curve.
18. **Physical validation:** all current laptopXbox→SABLE→network→Mini-PC items need supervised validation, including stand/sit, individual directions/curve/lateral, zero/RB/timeout/controller/network/reconnect/fresh engagement/ownership/takeover; autonomy later. Five PLANNED records link the individual matrix. No experiment executed.
19. **Future capture:** SABLE AGENTS.md and ENGINEERING_KNOWLEDGE_WORKFLOW.md locate canonical existing knowledge before relevant decisions; Lite AGENTS/tool workflow captures Test/Finding/evidence classes and failure sequences proportionately. Missing knowledge root is explicit, not a replacement baseline.
20. **Workflow proof:** external synthetic SAFETY dry run read canonical rules and matched records before deciding; created sandbox-only synthetic Test/Finding/indexes, validated links/schema. Report SYNTHETIC_WORKFLOW_PROOF_20261002.json retained; physical proof false, no commands. Synthetic records not inserted into canonical history. This proves tooling behavior, not guaranteed future agent compliance.
21. **Fleet future design:** FLEET_KNOWLEDGE_DESIGN.md specifies hardware/firmware/software/sensor/site/config/evidence/applicability/supersession and human acceptance; no fleet deployment or cross-robot calibration reuse implemented.
22. **Verification:** final results/file hashes are in evidence/SAFE_CLOSURE_VERIFICATION_20261002.json. Inert ROS tests/builds, mocked backend tests, frontend focused/full checks, canonical validators, synthetic workflow tests and branding checks run. No node launch/live robot graph or physical UDP test performed. Preserve initial failures and environment corrections in verification.
23. **Commits:** logical reviewed local commits recorded in final handoff/Git log. No push. Source and canonical evidence remain separate repositories; no shared history rewritten.
24. **Human action:** review diffs; inspect hardware/power safety; authorize deployment separately with effective version/config/guards verified; supply fresh read-only readiness envelope; then supervised stages A→B→C→D and separately approvedE. Capture exact path and all failures; calibration changes require new evidence, not assumptions.

| Concept | Disposition | SABLE owner | Validation / limit |
|---|---|---|---|
| Single driver/vendor encoding | B preserve existing abstraction | sable_lite3_bridge | No second writer |
| Historical gait/deadman/neutral knowledge | C reimplement through existing protected API | fleet/control agent/control authority/teleop and driver | Offline; current path physical retest |
| Local Xbox | D diagnostic evidence only | No new runtime owner | Laptop Xbox product target |
| CPU fallback | C | sable_navigation/stack.py | AVX unknown→RPP; unsafe forced MPPI refused; caps unchanged |
| Idle odom guard | C | lite3_bridge_node.py | Successful guarded nonzero dispatch only;0.5s configurable; yaw telemetry retained |
| Scaling observability | C | driver diagnostics + robot_telemetry_node | Local send not ACK; no calibration change |
| Virtual/laptop controls | C | existing shared teleop composables/DriveTab | Same API; real unknowns displayed |
| Historical lateral encoding | D as physical claim; B as existing code support | existing driver protocol |0x21010131 exists; direct strafe UNVALIDATED |
| Site speed/sign | D as default | configuration review only | Requires hardware calibration provenance |
| Passive validation tools | A/C | scripts/lite3_validation.py + runbook | File-only, operator-started filter; no turnkey live exporter |

## MINI-PC DEPLOYED-STATE AUDIT

Sources, artifacts, service/version/config discrepancies and provenance are detailed in MINIPC_DEPLOYED_STATE_AUDIT.md and61curated evidence records. Seven bag entries and payload availability are in BAG_EVIDENCE_CATALOG.md; site overrides classified in SITE_CONFIGURATION_RECONCILIATION.md. New read-only findings080–084 and subsequent source reconciliation095 retain their different scopes. Nothing deployed is assumed authoritative solely because installed.

MINI-PC ACCESSED: READ ONLY. MINI-PC FILES MODIFIED: NO. MINI-PC MODIFIED: NO. SERVICES MODIFIED: NO. MINI-PC SERVICES MODIFIED: NO. ROBOT OWNERSHIP ACQUIRED: NO. ROBOT COMMANDS SENT: NO. ROBOT MOTION: NONE. PHYSICAL MOTION EXECUTED: NO. PHYSICAL VALIDATION DEFERRED: YES.

## READY FOR RAZ SUPERVISED PHYSICAL VALIDATION

Preparation complete; **actual readiness NO**. Use SABLE docs/LITE3_PHYSICAL_VALIDATION.md for exact preflight command, documented localhost8000/app URL, laptop Xbox check, A/B steps, first≤0.05requested-x/≤0.3s pulse, stop sequence, evidence paths, each-item matrix, risks/prohibited tests and reviewed rollback procedure. No live exporter/deployment/hardware acceptance exists from this preparation. PHYSICAL ROBOT TESTS EXECUTED: NO. ROBOT MOTION: NONE. ROBOT OWNERSHIP ACQUIRED: NO. PHYSICAL TEST RECORDS: PLANNED ONLY.

## Reviewed SABLE local commits

- 2b268cc Document historical reconciliation and require evidence-based knowledge capture
- 9063369 Prepare laptop teleoperation evidence and supervised Lite3 validation
- d3a023f Reconcile Lite3 idle odometry and expose guarded command conversion evidence
- 82ef525 Support CPU-compatible navigation controller selection with bounded limits
