> **Continuation update2026-10-02:** the earlier record-gap metrics below preserve the initial audit. Current source-bound coverage is in the JSON and additional-capture manifest:92 scopes now have their appropriate record type(s); raw evidence gaps remain. This means historical claims are represented, not physically validated. Current total82 Test Sessions /54 Findings.

# Historical master inventory

Audited 2026-10-02: **92 independent event/campaign scopes**, plus 2 provenance aliases. The [complete JSON](HISTORICAL_MASTER_INVENTORY.json) preserves all fields, original record text, source dates, coverage, and failure/fix/retest stages. This concise ledger does not authorize hardware work or establish current readiness.

## Scope and reproducible counts

Local repository/Git, retained artifact CSVs, and three supplied primary PDFs were read without ROS calls, physical tests, or Mini-PC access by this reviewer. Root-owned Mini-PC evidence is appended separately. Canonical baseline coverage is frozen to Git `cc9cd690734428d4c38869ad5ddc530b6d75f7bf`; restored/new working-tree records are mapped separately as final coverage.

- Entries: 94; independent: 92; aliases: 2.
- Gap-audit crossmap: 53 entries; 37 matched existing scope, 11 appended independent scope, 5 reconstruction/capability gaps or root-owned additions at initial reconciliation.
- Baseline HEAD has 11 Test Sessions and 11 Findings. Non-HEAD `173f61d` has 23 Test Sessions and 21 Findings: 12 sessions and 10 findings absent baseline HEAD.

```python
import json
d = json.load(open("docs/engineering/HISTORICAL_MASTER_INVENTORY.json"))
assert sum(e["count_as_independent_event"] for e in d["events"]) == d["counts"]["independent_events"]
assert len(d["gap_audit_crossmap"]) == 53
```

Final canonical working-tree records: 56 Test Sessions and 43 Findings. Final independent-event coverage counts: {'FULLY': 63, 'MISSING FINDING': 4, 'MISSING BOTH': 6, 'MISSING TEST SESSION': 18, 'PARTIALLY': 1}. Raw evidence and physical retest limitations remain separate.

[Final knowledge gap audit](FINAL_KNOWLEDGE_GAP_AUDIT.md) · [Mini-PC deployed-state audit](MINIPC_DEPLOYED_STATE_AUDIT.md) · [SABLE integration closure audit](SABLE_INTEGRATION_CLOSURE_AUDIT.md)

## Chronology

| Period | Independent scopes | Evidence boundary |
|---|---:|---|
| AUGUST | 1 | Aug17 configuration commit; physical run evidence missing. |
| Sep1–7 | 0 | No independently dated retained event found; evidence gap, not proof of inactivity. |
| Sep8–14 | 12 | Sep13–14 low-level stand/RL/vendor work; Sep8–12 sparse. |
| Sep15–21 | 13 | ICP replay, supported stand/body shift/FR and model campaign. |
| Sep22–28 | 17 | Runtime, DDS, localization, navigation and resources; Sep22–25 sparse. |
| Sep29–Oct1 | 12 | Reconciliation and NOMAD stages; physical adapter acceptance absent. |
| current integration | 5 | Current separate existing-path NOMAD integration: offline only. |
| UNKNOWN date | 32 | Exact run timestamps absent; source/report dates preserved separately in JSON. |

A PDF date, commit date, or artifact mtime is not an experiment timestamp. Preserve unknown dates and missing deployed manifests. Primary PDF B still reports Day 2 autonomous acceptance OPEN; the subsequent contemporary closeout records interruption then PASS. Both remain chronology-specific evidence.

**Direct strafe has no PASS.** The previous NOMAD failure has root cause UNKNOWN. Older ROS lateral `y=0` was disabled; arcs and chair displacement do not prove pure body-frame lateral locomotion. Source implements body-only 30/60/90 safe fractions; per-level hardware evidence is incomplete, and the later proposed 25/50/75 model-validation plan is different.

## Coverage and deduplication

Final `expected_record_kinds` is event-specific: ordinary experiment/accepted-stage scopes require a Test Session; pure protocol/configuration concepts require a Finding; independent failure/correction lessons require both. Optional kinds never inflate missing counts. Baseline `coverage_status` records dedicated canonical HEAD Test Session/Finding presence. `evidence_completeness` is independent. Related aggregate or planned records do not count as direct incident coverage. `final_coverage_*` fields, when present, describe restored/new canonical records and leave baseline truth unchanged.

HIST-034 folds into HIST-068/069; HIST-052 folds into HIST-075. Both are provenance aliases and excluded from independent counts. HIST-003 physical failure and HIST-026 inert recovery are different executions. HIST-012 later permit-hypothesis guard abort and HIST-037 earlier raw-speed abort are distinct. HIST-076 unsafe approval-start claim and HIST-018 corrected offline test are distinct. RMS hold-loss persistence, atomic authorization, absolute hold deadline, raw body-shift speed guard and high-level temporary lease are different defects.

## Concise event ledger


### AUGUST


#### HIST-024 — Wi-Fi name configuration baseline

- **Date / result / evidence:** 2026-08-17 / SOURCE_CHANGE / COMMITTED_SOURCE.
- **Objective/configuration:** NETWORKING; c243294.
- **Execution/observation:** Source configuration changed; no physical/network validation established
- **Cause → fix → retest:** UNKNOWN → Configuration names updated → UNKNOWN.
- **Lesson/status:** Commit dates do not date hardware sessions; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence FULLY. Direct NONE. Related only NONE.
- **Sources:** `git c243294`.
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING FINDING; expected FINDING; NONE.

### Sep1–7

EVIDENCE MISSING: no independently dated event found.

### Sep8–14


#### HIST-001 — Long supported stand and controlled release

- **Date / result / evidence:** 2026-09-13 / PASS / PHYSICALLY_PROVEN.
- **Objective/configuration:** ROBOT_CONTROL, SAFETY, R_AND_D; SHA ac56328; robot UNKNOWN.
- **Execution/observation:** Robot held TARGET_REACHED for about 203 seconds and returned to lying after explicit release
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct [TEST-20260913-001](tests/TEST-20260913-001-long-supported-stand-release.md). Related only NONE.
- **Sources:** [TEST-20260913-001-long-supported-stand-release.md](tests/TEST-20260913-001-long-supported-stand-release.md) @173f61d.
- **Remaining gap:** MISSING BOTH; Recover existing IDs TEST-20260913-001. RESTORE existing non-HEAD record; do not mint duplicate ID.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20260913-001](tests/TEST-20260913-001-long-supported-stand-release.md).

#### HIST-002 — Bounded RL-zero and stop release

- **Date / result / evidence:** 2026-09-13 / PASS / PHYSICALLY_PROVEN.
- **Objective/configuration:** ROBOT_CONTROL, SAFETY, R_AND_D; SHA ac56328; robot UNKNOWN.
- **Execution/observation:** Two supported zero-input RL runs remained stable and released safely
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct [TEST-20260913-002](tests/TEST-20260913-002-rl-zero-bounded-release.md). Related only NONE.
- **Sources:** [TEST-20260913-002-rl-zero-bounded-release.md](tests/TEST-20260913-002-rl-zero-bounded-release.md) @173f61d.
- **Remaining gap:** MISSING BOTH; Recover existing IDs TEST-20260913-002. RESTORE existing non-HEAD record; do not mint duplicate ID.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20260913-002](tests/TEST-20260913-002-rl-zero-bounded-release.md).

#### HIST-003 — First supervised stand guard rejection

- **Date / result / evidence:** 2026-09-13 / FAIL / FAILED.
- **Objective/configuration:** ROBOT_CONTROL, SAFETY, R_AND_D; SHA ac56328; robot UNKNOWN.
- **Execution/observation:** Stand entered STANDING_UP then aborted with send guard rejected output
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct [TEST-20260913-003](tests/TEST-20260913-003-first-supervised-stand-failure.md). Related only NONE.
- **Sources:** [TEST-20260913-003-first-supervised-stand-failure.md](tests/TEST-20260913-003-first-supervised-stand-failure.md) @173f61d.
- **Remaining gap:** MISSING BOTH; Recover existing IDs TEST-20260913-003. RESTORE existing non-HEAD record; do not mint duplicate ID.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20260913-003](tests/TEST-20260913-003-first-supervised-stand-failure.md).

#### HIST-004 — Bounded vendor manual-axis forward pulse

- **Date / result / evidence:** 2026-09-14 / PASS / PHYSICALLY_PROVEN.
- **Objective/configuration:** ROBOT_CONTROL, SAFETY, XBOX; SHA ac56328; robot UNKNOWN.
- **Execution/observation:** A bounded external SimpleCMD pulse produced operator-confirmed forward locomotion and neutral recovery
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct [TEST-20260914-001](tests/TEST-20260914-001-vendor-manual-axis-forward.md), [FINDING-20260914-001](findings/FINDING-20260914-001-vendor-manual-axis-protocol.md). Related only NONE.
- **Sources:** [TEST-20260914-001-vendor-manual-axis-forward.md](tests/TEST-20260914-001-vendor-manual-axis-forward.md) @173f61d.
- **Remaining gap:** MISSING BOTH; Recover existing IDs TEST-20260914-001, FINDING-20260914-001. RESTORE existing non-HEAD record; do not mint duplicate ID.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20260914-001](tests/TEST-20260914-001-vendor-manual-axis-forward.md), [FINDING-20260914-001](findings/FINDING-20260914-001-vendor-manual-axis-protocol.md).

#### HIST-026 — Inert first stand failure recovery

- **Date / result / evidence:** 2026-09-13 / PASS / OFFLINE_PROVEN.
- **Objective/configuration:** SAFETY; historical dirty base preserved ac56328.
- **Execution/observation:** Double monotonic clock fixes collapsed float millisecond times at2million seconds; frozen plant abort .435s synthetic
- **Cause → fix → retest:** Offline timing/snapshot/preflight defects; historical physical first cause UNKNOWN → Double clock, snapshots, rejection diagnostics → Five focused CTest plus startup regression;23,739records/28traces.
- **Lesson/status:** Synthetic tracking failure is not historical robot diagnosis; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence FULLY. Direct NONE. Related only [TEST-20260913-003](tests/TEST-20260913-003-first-supervised-stand-failure.md).
- **Sources:** [EXPERIMENTS.md](../EXPERIMENTS.md); [STAND_RECOVERY_2026-09-13.md](../STAND_RECOVERY_2026-09-13.md).
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING BOTH; expected TEST_SESSION, FINDING; NONE.

#### HIST-027 — Normal lying posture passive reset

- **Date / result / evidence:** 2026-09-13 / PASS / LIVE_STATIC_REPORT_AND_RETAINED_CSV.
- **Objective/configuration:** HARDWARE; Unchanged signs/limits/targets.
- **Execution/observation:** 34999callbacks, maxage1.63351ms; right HipY out-of-range disappeared, all near-1.15rad
- **Cause → fix → retest:** Posture/startup dependence supported; reset factor unresolved → Human preparation; no mapping patch → Passive console preflight OK.
- **Lesson/status:** Raw telemetry alone cannot identify posture; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct [FINDING-20260913-002](findings/FINDING-20260913-002-posture-dependent-joint-readings.md). Related only NONE.
- **Sources:** [normal-lying-observation.csv](../handoff_evidence/20260913/normal-lying-observation.csv); [EXPERIMENTS.md](../EXPERIMENTS.md).
- **Remaining gap:** MISSING BOTH; Recover existing IDs FINDING-20260913-002. Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** FULLY; expected FINDING; [FINDING-20260913-002](findings/FINDING-20260913-002-posture-dependent-joint-readings.md).

#### HIST-028 — Convergence and supported stand entry

- **Date / result / evidence:** 2026-09-13 / PASS / HISTORICAL_OPERATOR_REPORT.
- **Objective/configuration:** SAFETY; RMS50ms and positionrange.
- **Execution/observation:** Operator standing held; original isolated speed spike resets avoided
- **Cause → fix → retest:** Convergence too sensitive to isolated speeds; authorization timing → Atomic entry and RMS/position convergence → E7 release; E8 long hold.
- **Lesson/status:** Hold policy changed later; preserve original build evidence; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only [TEST-20260913-001](tests/TEST-20260913-001-long-supported-stand-release.md).
- **Sources:** [EXPERIMENTS.md](../EXPERIMENTS.md); [STAND_CONVERGENCE_REVIEW_2026-09-13.md](../STAND_CONVERGENCE_REVIEW_2026-09-13.md).
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION; NONE.

#### HIST-029 — Policy contract comparison and restoration

- **Date / result / evidence:** 2026-09-14 / PASS_OFFLINE_ONLY / OFFLINE_REPORT.
- **Objective/configuration:** R_AND_D; January12ms paired-.80/1.60 versus April20ms paired-.65/1.30; Kp30/Kd1.
- **Execution/observation:** January.996m versus April.619m; April posture-only at60percent actuator
- **Cause → fix → retest:** Plant response insufficient in modeled weak-actuator family → Restore coherent January contract → Hardware still failed useful locomotion.
- **Lesson/status:** Never mix policy pose timing/action history contracts; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence FULLY. Direct [FINDING-20260914-002](findings/FINDING-20260914-002-direct-onnx-not-pilot.md). Related only NONE.
- **Sources:** [POLICY_GAIT_ROOT_CAUSE_2026-09-14.md](../POLICY_GAIT_ROOT_CAUSE_2026-09-14.md).
- **Remaining gap:** MISSING BOTH; Recover existing IDs FINDING-20260914-002. Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION, FINDING; [FINDING-20260914-002](findings/FINDING-20260914-002-direct-onnx-not-pilot.md).

#### HIST-030 — Direct ONNX forward trials

- **Date / result / evidence:** 2026-09-14 / FAIL / HISTORICAL_PHYSICAL_REPORT.
- **Objective/configuration:** R_AND_D; Coherent policy/pose/timing; bounded joint-level path.
- **Execution/observation:** Hardware knee .014-.030rad; lean/stepping/falls/releases; no safe useful translation
- **Cause → fix → retest:** Unresolved sim-to-real dynamics/tracking; precise physical cause UNKNOWN → Paused product ONNX; vendor gait selected → Vendor forward pulse physically reported separately.
- **Lesson/status:** Kinematic/software agreement cannot prove plant authority; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct [FINDING-20260914-002](findings/FINDING-20260914-002-direct-onnx-not-pilot.md). Related only NONE.
- **Sources:** [HIGH_LEVEL_CONTROL_INVESTIGATION_2026-09-14.md](../HIGH_LEVEL_CONTROL_INVESTIGATION_2026-09-14.md); [POLICY_GAIT_ROOT_CAUSE_2026-09-14.md](../POLICY_GAIT_ROOT_CAUSE_2026-09-14.md).
- **Remaining gap:** MISSING BOTH; Recover existing IDs FINDING-20260914-002. Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION, FINDING; [FINDING-20260914-002](findings/FINDING-20260914-002-direct-onnx-not-pilot.md).

#### HIST-031 — Reject legacy vendor command hypotheses

- **Date / result / evidence:** 2026-09-14 / FAIL_THEN_OFFLINE_FIX / HISTORICAL_REPORT_AND_STATIC_SOURCE.
- **Objective/configuration:** ROBOT_CONTROL; Robot-matched deeprcs/library static hashes.
- **Execution/observation:** Legacy commands did not locomote; bare0130 caught before live by source-mask check
- **Cause → fix → retest:** Matched path requires21000000 mask and normalized manual-axis encoding → Full21010130/131/135, deadzone6553 and asymmetric divisor → Offline exact bytes/no network; first physical forward later.
- **Lesson/status:** Do not retry firmware-unqualified codes; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence FULLY. Direct [FINDING-20260914-001](findings/FINDING-20260914-001-vendor-manual-axis-protocol.md). Related only NONE.
- **Sources:** [HIGH_LEVEL_CONTROL_INVESTIGATION_2026-09-14.md](../HIGH_LEVEL_CONTROL_INVESTIGATION_2026-09-14.md); [EXPERIMENTS.md](../EXPERIMENTS.md).
- **Remaining gap:** MISSING BOTH; Recover existing IDs FINDING-20260914-001. Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** FULLY; expected FINDING; [FINDING-20260914-001](findings/FINDING-20260914-001-vendor-manual-axis-protocol.md).

#### HIST-032 — Original vendor controller transport investigation

- **Date / result / evidence:** 2026-09-14 / INCONCLUSIVE / PASSIVE_REPORT_AND_STATIC_ANALYSIS.
- **Objective/configuration:** SENSORS; Passive captured original-controller successful movement.
- **Execution/observation:** ttyS6 Yesense IMU; ttyS3 battery; ttyS1 ultrasound/heat; only heartbeat UDP visible; axis ingress UNKNOWN
- **Cause → fix → retest:** Original controller axis transport remains UNKNOWN → Use separately proven external manual axes → Forward source-backed pulse.
- **Lesson/status:** Heartbeat capture is not axis transport proof; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only [FINDING-20260914-001](findings/FINDING-20260914-001-vendor-manual-axis-protocol.md).
- **Sources:** [HIGH_LEVEL_CONTROL_INVESTIGATION_2026-09-14.md](../HIGH_LEVEL_CONTROL_INVESTIGATION_2026-09-14.md).
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING BOTH; expected TEST_SESSION, FINDING; NONE.

#### HIST-033 — Repeat bounded manual-axis forward

- **Date / result / evidence:** 2026-09-14 / PARTIAL / HISTORICAL_SOFTWARE_REPORT.
- **Objective/configuration:** ROBOT_CONTROL; Raw9174 normalized+.099985,.30s,20Hz.
- **Execution/observation:** 51records;final6/0/0,battery56percent; no independent translation report
- **Cause → fix → retest:** UNKNOWN → NONE → No separate observation.
- **Lesson/status:** Repeat software completion is not additional physical proof; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct [FINDING-20260914-001](findings/FINDING-20260914-001-vendor-manual-axis-protocol.md). Related only NONE.
- **Sources:** [EXPERIMENTS.md](../EXPERIMENTS.md).
- **Remaining gap:** MISSING BOTH; Recover existing IDs FINDING-20260914-001. Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION; [FINDING-20260914-001](findings/FINDING-20260914-001-vendor-manual-axis-protocol.md).

### Sep15–21


#### HIST-005 — ICP baseline rejection and null-guess cascade

- **Date / result / evidence:** 2026-09-15 / FAIL / FAILED.
- **Objective/configuration:** ODOMETRY, ROS2, R_AND_D; SHA f765a2b; robot UNKNOWN.
- **Execution/observation:** Baseline replay stopped odometry after a 0.646 correspondence ratio was rejected by the 0.70 threshold
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING TEST SESSION; evidence FULLY. Direct [TEST-20260915-001](tests/TEST-20260915-001-icp-baseline-null-guess.md), [FINDING-20260915-001](findings/FINDING-20260915-001-icp-null-guess.md). Related only NONE.
- **Sources:** [TEST-20260915-001-icp-baseline-null-guess.md](tests/TEST-20260915-001-icp-baseline-null-guess.md) @173f61d.
- **Remaining gap:** MISSING TEST SESSION; Recover existing IDs TEST-20260915-001. RESTORE existing non-HEAD record; do not mint duplicate ID.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [TEST-20260915-001](tests/TEST-20260915-001-icp-baseline-null-guess.md), [FINDING-20260915-001](findings/FINDING-20260915-001-icp-null-guess.md).

#### HIST-006 — ICP correspondence-threshold replay candidates

- **Date / result / evidence:** 2026-09-15 / PASS / OFFLINE_PROVEN.
- **Objective/configuration:** ODOMETRY, ROS2, R_AND_D; SHA f765a2b; robot UNKNOWN.
- **Execution/observation:** Ratio 0.30 and 0.50 replay candidates completed the selected motion windows without null-guess failure
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING TEST SESSION; evidence FULLY. Direct [TEST-20260915-002](tests/TEST-20260915-002-icp-threshold-candidates.md), [FINDING-20260915-001](findings/FINDING-20260915-001-icp-null-guess.md). Related only NONE.
- **Sources:** [TEST-20260915-002-icp-threshold-candidates.md](tests/TEST-20260915-002-icp-threshold-candidates.md) @173f61d.
- **Remaining gap:** MISSING TEST SESSION; Recover existing IDs TEST-20260915-002. RESTORE existing non-HEAD record; do not mint duplicate ID.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [TEST-20260915-002](tests/TEST-20260915-002-icp-threshold-candidates.md), [FINDING-20260915-001](findings/FINDING-20260915-001-icp-null-guess.md).

#### HIST-007 — Supported Stand and safe release

- **Date / result / evidence:** 2026-09-17 / PASS / PHYSICALLY_PROVEN.
- **Objective/configuration:** ROBOT_CONTROL, SAFETY; SHA 193cbc9; robot UNKNOWN.
- **Execution/observation:** The guarded supported-stand path produced telemetry-confirmed standing and returned to the safe released state without planar motion. Exact robot ID, site, and complete deployment manifest are `UNKNOWN`.
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING FINDING; evidence EVIDENCE INCOMPLETE. Direct [TEST-20260917-001](tests/TEST-20260917-001-supported-stand.md), [FINDING-20260917-002](findings/FINDING-20260917-002-absolute-stand-hold-deadline.md). Related only NONE.
- **Sources:** [TEST-20260917-001-supported-stand.md](tests/TEST-20260917-001-supported-stand.md) @173f61d.
- **Remaining gap:** MISSING FINDING; Recover existing IDs FINDING-20260917-002. Existing record at HEAD.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20260917-001](tests/TEST-20260917-001-supported-stand.md), [FINDING-20260917-002](findings/FINDING-20260917-002-absolute-stand-hold-deadline.md).

#### HIST-008 — Separate stand authorization expired before request

- **Date / result / evidence:** 2026-09-17 / FAIL / FAILED.
- **Objective/configuration:** ROBOT_CONTROL, SAFETY, R_AND_D; SHA 2568136; robot UNKNOWN.
- **Execution/observation:** Five-second authorization expired before stand input; the robot did not move and the gate stayed closed
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence FULLY. Direct [TEST-20260917-002](tests/TEST-20260917-002-stand-authorization-expiry.md), [FINDING-20260917-001](findings/FINDING-20260917-001-atomic-stand-authorization.md). Related only NONE.
- **Sources:** [TEST-20260917-002-stand-authorization-expiry.md](tests/TEST-20260917-002-stand-authorization-expiry.md) @173f61d.
- **Remaining gap:** MISSING BOTH; Recover existing IDs TEST-20260917-002, FINDING-20260917-001. RESTORE existing non-HEAD record; do not mint duplicate ID.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [TEST-20260917-002](tests/TEST-20260917-002-stand-authorization-expiry.md), [FINDING-20260917-001](findings/FINDING-20260917-001-atomic-stand-authorization.md).

#### HIST-009 — Supported stand automatic release

- **Date / result / evidence:** 2026-09-17 / PARTIAL / PARTIAL.
- **Objective/configuration:** ROBOT_CONTROL, SAFETY, R_AND_D; SHA 11b5ad4; robot UNKNOWN.
- **Execution/observation:** Software trace passed the two-second automatic-release contract; operator reported normal stand and return but independent physical evidence is incomplete
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct [TEST-20260917-003](tests/TEST-20260917-003-stand-automatic-release.md), [FINDING-20260917-002](findings/FINDING-20260917-002-absolute-stand-hold-deadline.md). Related only NONE.
- **Sources:** [TEST-20260917-003-stand-automatic-release.md](tests/TEST-20260917-003-stand-automatic-release.md) @173f61d.
- **Remaining gap:** MISSING BOTH; Recover existing IDs TEST-20260917-003, FINDING-20260917-002. RESTORE existing non-HEAD record; do not mint duplicate ID.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [TEST-20260917-003](tests/TEST-20260917-003-stand-automatic-release.md), [FINDING-20260917-002](findings/FINDING-20260917-002-absolute-stand-hold-deadline.md).

#### HIST-010 — Supported body-shift physical progression

- **Date / result / evidence:** 2026-09-18 / PASS / HISTORICAL_CLAIM.
- **Objective/configuration:** ROBOT_CONTROL, SAFETY, R_AND_D; SHA fe22943; robot UNKNOWN.
- **Execution/observation:** Handoff records report successful 6 mm, 10 mm, and 15 mm supported shifts
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct [TEST-20260918-001](tests/TEST-20260918-001-body-shift-progression.md). Related only NONE.
- **Sources:** [TEST-20260918-001-body-shift-progression.md](tests/TEST-20260918-001-body-shift-progression.md) @173f61d.
- **Remaining gap:** MISSING BOTH; Recover existing IDs TEST-20260918-001. RESTORE existing non-HEAD record; do not mint duplicate ID.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20260918-001](tests/TEST-20260918-001-body-shift-progression.md).

#### HIST-011 — Supported front-right leg-lift attempts

- **Date / result / evidence:** 2026-09-18 / PARTIAL / PARTIAL.
- **Objective/configuration:** ROBOT_CONTROL, SAFETY, R_AND_D; SHA fe22943; robot UNKNOWN.
- **Execution/observation:** Correct-direction joint motion occurred but no visible foot clearance was established
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct [TEST-20260918-002](tests/TEST-20260918-002-fr-leg-lift-attempts.md), [FINDING-20260918-001](findings/FINDING-20260918-001-low-level-foot-force-unavailable.md). Related only NONE.
- **Sources:** [TEST-20260918-002-fr-leg-lift-attempts.md](tests/TEST-20260918-002-fr-leg-lift-attempts.md) @173f61d.
- **Remaining gap:** MISSING BOTH; Recover existing IDs TEST-20260918-002, FINDING-20260918-001. RESTORE existing non-HEAD record; do not mint duplicate ID.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [TEST-20260918-002](tests/TEST-20260918-002-fr-leg-lift-attempts.md), [FINDING-20260918-001](findings/FINDING-20260918-001-low-level-foot-force-unavailable.md).

#### HIST-012 — Supported body-shift guard abort

- **Date / result / evidence:** 2026-09-18 / FAIL / FAILED.
- **Objective/configuration:** ROBOT_CONTROL, SAFETY, R_AND_D; SHA fe22943; robot UNKNOWN.
- **Execution/observation:** A physical body-shift action aborted before leg lift with supported body shift guard failure
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct [TEST-20260918-003](tests/TEST-20260918-003-body-shift-guard-abort.md), [FINDING-20260918-002](findings/FINDING-20260918-002-long-action-permit-lifecycle.md). Related only NONE.
- **Sources:** [TEST-20260918-003-body-shift-guard-abort.md](tests/TEST-20260918-003-body-shift-guard-abort.md) @173f61d.
- **Remaining gap:** MISSING BOTH; Recover existing IDs TEST-20260918-003, FINDING-20260918-002. RESTORE existing non-HEAD record; do not mint duplicate ID.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [TEST-20260918-003](tests/TEST-20260918-003-body-shift-guard-abort.md), [FINDING-20260918-002](findings/FINDING-20260918-002-long-action-permit-lifecycle.md).

#### HIST-013 — Front-right robust unload simulation campaign

- **Date / result / evidence:** 2026-09-21 / FAIL / FAILED.
- **Objective/configuration:** ROBOT_CONTROL, SAFETY, R_AND_D; SHA 25b9865; robot NOT_APPLICABLE.
- **Execution/observation:** Eighty nominal candidates produced zero robust unload passes; lift search was not started
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence FULLY. Direct [TEST-20260921-001](tests/TEST-20260921-001-fr-robust-unload-campaign.md), [FINDING-20260921-001](findings/FINDING-20260921-001-simulation-contact-model-ambiguity.md). Related only NONE.
- **Sources:** [TEST-20260921-001-fr-robust-unload-campaign.md](tests/TEST-20260921-001-fr-robust-unload-campaign.md) @173f61d.
- **Remaining gap:** MISSING BOTH; Recover existing IDs TEST-20260921-001, FINDING-20260921-001. RESTORE existing non-HEAD record; do not mint duplicate ID.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [TEST-20260921-001](tests/TEST-20260921-001-fr-robust-unload-campaign.md), [FINDING-20260921-001](findings/FINDING-20260921-001-simulation-contact-model-ambiguity.md).

#### HIST-034 — Backward yaw and arcs prior ROS vendor path

- **Date / result / evidence:** 2026-09-16 / HISTORICAL_CLAIM / SECONDARY_HANDOFF_REPORT.
- **Objective/configuration:** ROBOT_CONTROL; Historical abx/ros2_ws handoff; exact SHA UNKNOWN.
- **Execution/observation:** Physical directional success claimed; primary ROBOT_HANDOFF absent; historical ROS lateral disabled y0
- **Cause → fix → retest:** UNKNOWN → Vendor gait product path chosen → Current adapter acceptance remains separate.
- **Lesson/status:** Do not infer strafe from arcs or world displacement; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** PARTIALLY; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only [FINDING-20260914-001](findings/FINDING-20260914-001-vendor-manual-axis-protocol.md), [TEST-20260927-004](tests/TEST-20260927-004-laptop-xbox-manual.md).
- **Sources:** [ROS_VENDOR_GAIT_HANDOFF_2026-09-16.md](../ROS_VENDOR_GAIT_HANDOFF_2026-09-16.md).
- **Remaining gap:** PARTIALLY; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Counting:** provenance alias; excluded from independent count.
- **Final coverage:** PARTIALLY; expected ; NONE.

#### HIST-035 — One-leg kinematics and deterministic simulation

- **Date / result / evidence:** 2026-09-17 / PASS / OFFLINE_SIMULATION_REPORT.
- **Objective/configuration:** R_AND_D; Pinned MJCF b452a1f;MuJoCo2.2.2;PD180/3.5,sphere-only contacts.
- **Execution/observation:** FK1.01e-16m;IK<1e-7m;6.4315mm clearance;100percentunload/restoredcontacts
- **Cause → fix → retest:** Native shank meshes overlap sphere by.5mm → Runtime sphere-only contact normalization → Two deterministic PASS; later bounded campaigns fail.
- **Lesson/status:** Simulation-only normalized contact/gains never hardware approval; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence PARTIALLY. Direct NONE. Related only [FINDING-20260921-001](findings/FINDING-20260921-001-simulation-contact-model-ambiguity.md).
- **Sources:** [ONE_LEG_LIFT_SIMULATION.md](../ONE_LEG_LIFT_SIMULATION.md); `git fc5fe7e`.
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION; NONE.

#### HIST-036 — Supported FR path offline construction

- **Date / result / evidence:** 2026-09-18 / PASS / OFFLINE_PROVEN.
- **Objective/configuration:** R_AND_D; 5mm shift,2mmlift,.25shold;kp<=60,kd<=.7.
- **Execution/observation:** 2/2focusedtests,finite IK targets,abort/release path; hardware not executed for this milestone
- **Cause → fix → retest:** UNKNOWN → Bounded separate action → Physical runs separately reported.
- **Lesson/status:** Offline path readiness cannot establish unloading; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence PARTIALLY. Direct NONE. Related only [TEST-20260918-002](tests/TEST-20260918-002-fr-leg-lift-attempts.md), [FINDING-20260918-001](findings/FINDING-20260918-001-low-level-foot-force-unavailable.md).
- **Sources:** [HANDOFF_SUPPORTED_LEG_LIFT_2026-09-18.md](../HANDOFF_SUPPORTED_LEG_LIFT_2026-09-18.md); `git eb63a36`.
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION; NONE.

#### HIST-037 — Real body-shift measured-speed guard abort

- **Date / result / evidence:** 2026-09-18 / FAIL / HISTORICAL_PHYSICAL_TRACE_ANALYSIS_REPORT.
- **Objective/configuration:** SAFETY; Abruptkp100/2.5→60/.7;5mm plan.
- **Execution/observation:** FLkneemeasured.514640808rad/s exceeds.50;real short oscillatory excursion
- **Cause → fix → retest:** Gain discontinuity correlated, causal root UNKNOWN → Compare A abrupt Bstandgains Csmooth;select B without relaxing limits → Offline maxdelta.0229582rad,maxspeed.0215233rad/s.
- **Lesson/status:** Keep real guard failure; remove discontinuity before causal claim; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only [TEST-20260918-003](tests/TEST-20260918-003-body-shift-guard-abort.md), [FINDING-20260918-002](findings/FINDING-20260918-002-long-action-permit-lifecycle.md).
- **Sources:** [BODY_SHIFT_OFFLINE_REVIEW_2026-09-18.md](../BODY_SHIFT_OFFLINE_REVIEW_2026-09-18.md).
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING BOTH; expected TEST_SESSION, FINDING; NONE.

#### HIST-038 — Passive vendor gait and foot-force contrast

- **Date / result / evidence:** 2026-09-18 / PARTIAL / HISTORICAL_PASSIVE_REPORT.
- **Objective/configuration:** SENSORS; Receiver-only original remote ownership;~1000Hz.
- **Execution/observation:** Diagonal/trot coordination;FRHipY-.18to-.38rad,knee+.25to+.40;forces usefulvendor/zero lowlevel
- **Cause → fix → retest:** Zero low-level force reason UNKNOWN → Require calibrated independent loads → No calibrated hardware unload proof.
- **Lesson/status:** Do not copy isolated threeleg FR from trot; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct [FINDING-20260918-001](findings/FINDING-20260918-001-low-level-foot-force-unavailable.md). Related only NONE.
- **Sources:** [HANDOFF_2026-09-18_LEG_LIFT.md](../handoff/HANDOFF_2026-09-18_LEG_LIFT.md).
- **Remaining gap:** MISSING BOTH; Recover existing IDs FINDING-20260918-001. Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION, FINDING; [FINDING-20260918-001](findings/FINDING-20260918-001-low-level-foot-force-unavailable.md).

### Sep22–28


#### HIST-014 — Chair avoidance attempt interrupted by power loss

- **Date / result / evidence:** 2026-09-27 / PARTIAL / PARTIAL.
- **Objective/configuration:** NAVIGATION, SAFETY, HARDWARE; SHA abf9900; robot robot_01.
- **Execution/observation:** The Lite3 detected and passed the chair and travelled about 1.64 m with localization around 92%, exercising forward/lateral/yaw through the product path. Mini-PC power/link interruption prevented proof of terminal goal result and final release, so this is not a PASS.
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING FINDING; evidence EVIDENCE INCOMPLETE. Direct [TEST-20260927-001](tests/TEST-20260927-001-chair-avoidance-interrupted.md). Related only NONE.
- **Sources:** [TEST-20260927-001-chair-avoidance-interrupted.md](tests/TEST-20260927-001-chair-avoidance-interrupted.md) @173f61d.
- **Remaining gap:** MISSING FINDING; Existing record at HEAD.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20260927-001](tests/TEST-20260927-001-chair-avoidance-interrupted.md).

#### HIST-015 — Accepted physical Nav2 chair avoidance

- **Date / result / evidence:** 2026-09-27 / PASS / PHYSICALLY_PROVEN.
- **Objective/configuration:** NAVIGATION, LOCALIZATION, SAFETY, SENSORS; SHA abf9900; robot robot_01.
- **Execution/observation:** LiDAR/costmaps detected a real chair; Nav2 selected a right-side path of about 1.47 m; `NavigateToPose` returned `SUCCEEDED` (`error_code=0`); the robot cleared the chair without recorded contact and stopped. Final localization was about 95.4%, AUTONOMY released, and final `COMMAND_SOURCE=NONE`.
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING FINDING; evidence EVIDENCE INCOMPLETE. Direct [TEST-20260927-002](tests/TEST-20260927-002-chair-avoidance-pass.md). Related only NONE.
- **Sources:** [TEST-20260927-002-chair-avoidance-pass.md](tests/TEST-20260927-002-chair-avoidance-pass.md) @173f61d.
- **Remaining gap:** MISSING FINDING; Existing record at HEAD.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20260927-002](tests/TEST-20260927-002-chair-avoidance-pass.md).

#### HIST-016 — Home_Map localization acceptance gate

- **Date / result / evidence:** 2026-09-27 / PASS / LIVE_STATIC_PROVEN.
- **Objective/configuration:** LOCALIZATION, TF, SENSORS; SHA abf9900; robot robot_01.
- **Execution/observation:** The saved map, LiDAR alignment, AMCL pose, and required TF chain supported the three-consecutive-sample `>=80%` navigation gate. The accepted chair session ended around 95.4%. Saved pose is only an initial hypothesis; global fallback and short operator-assisted disambiguation remain part of the documented flow.
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING FINDING; evidence EVIDENCE INCOMPLETE. Direct [TEST-20260927-003](tests/TEST-20260927-003-home-map-localization.md). Related only NONE.
- **Sources:** [TEST-20260927-003-home-map-localization.md](tests/TEST-20260927-003-home-map-localization.md) @173f61d.
- **Remaining gap:** MISSING FINDING; Existing record at HEAD.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20260927-003](tests/TEST-20260927-003-home-map-localization.md).

#### HIST-017 — Laptop Xbox guarded manual control path

- **Date / result / evidence:** 2026-09-27 / PASS / PHYSICALLY_PROVEN.
- **Objective/configuration:** XBOX, ROBOT_CONTROL, SAFETY; SHA abf9900; robot robot_01.
- **Execution/observation:** Existing project records classify the laptop Xbox/C2 path and safe release as physically proven during manual localization/posture work. It used the exclusive `LAPTOP_XBOX` source rather than a second low-level controller.
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING FINDING; evidence EVIDENCE INCOMPLETE. Direct [TEST-20260927-004](tests/TEST-20260927-004-laptop-xbox-manual.md). Related only NONE.
- **Sources:** [TEST-20260927-004-laptop-xbox-manual.md](tests/TEST-20260927-004-laptop-xbox-manual.md) @173f61d.
- **Remaining gap:** MISSING FINDING; Existing record at HEAD.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20260927-004](tests/TEST-20260927-004-laptop-xbox-manual.md).

#### HIST-045 — Stationary localization ambiguity

- **Date / result / evidence:** 2026-09-26 / PARTIAL / HISTORICAL_LIVE_REPORT.
- **Objective/configuration:** LOCALIZATION; Home_Map;normal80percentx3.
- **Execution/observation:** Stalled55.1percent216/392hits;~20degand20-30cmmanual reported recovery
- **Cause → fix → retest:** Wrong/ambiguous hypothesis; not sensoroutage → Manual rotation/translation after AMCLactive → 98.4-98.9percent12samples afterDDSfix, separate incident.
- **Lesson/status:** Saved pose is hypothesis, confidence not probability; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only [TEST-20260927-003](tests/TEST-20260927-003-home-map-localization.md).
- **Sources:** `onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md`.
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20261002-029](tests/TEST-20261002-029-stationary-saved-pose-hypothesis-exhausted-at-55-1-percent.md).

#### HIST-046 — DDS and AMCL false-ready recovery

- **Date / result / evidence:** 2026-09-26 / FAIL_THEN_PASS / HISTORICAL_LIVE_SOFTWARE_REPORT.
- **Objective/configuration:** ROS2; Domain0;UDPV4 alternative.
- **Execution/observation:** Services active/oldsubscribertraffic whilenew scan/odom/TF invisible;UDPV4readytrue
- **Cause → fix → retest:** DDSdiscovery/SHM and lifecycle-beforeinputs → UDPV4gate/env,orderedreadiness/retries → 12confidence98.4-98.9samples;dry10cm3poses;units thenpending.
- **Lesson/status:** Do not restart robot heartbeat runtime to repair localization; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING TEST SESSION; evidence FULLY. Direct [FINDING-20260927-001](findings/FINDING-20260927-001-systemd-active-ros-dead.md). Related only NONE.
- **Sources:** `onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md`; [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- **Remaining gap:** MISSING TEST SESSION; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [FINDING-20260927-001](findings/FINDING-20260927-001-systemd-active-ros-dead.md), [TEST-20261002-001](tests/TEST-20261002-001-dds-recovery-with-incomplete-persistent-deployment.md), [TEST-20261002-002](tests/TEST-20261002-002-high-level-ros-readiness-failure-and-software-recovery.md), [TEST-20261002-026](tests/TEST-20261002-026-map-server-and-amcl-ordered-lifecycle-recovery.md).
- **Supplemental scope:** systemd active while runtime ROS participant disappeared: failure: Process active but node/topics/DDS or fresh telemetry absent.; fix/retest: Real graph/freshness health and bounded watchdog/restart; ordered startup..
- **Supplemental scope:** MapServer/AMCL startup transition failure: failure: Lifecycle timed out, amcl_pose/map→odom absent, confidence0 despite active units.; fix/retest: Network/DDS→runtime→freshscan/odom→MapServerACTIVE→AMCLACTIVE→TF→score; bounded retry/localization-only restart..

#### HIST-047 — Battery exhausted shutdown

- **Date / result / evidence:** 2026-09-26 / FAIL_OPERATIONAL / HISTORICAL_PHYSICAL_REPORT.
- **Objective/configuration:** HARDWARE; HistoricalDay1/Day2.
- **Execution/observation:** Ping/SSHoffline;C2robot_statusmissing;robotbatteryended
- **Cause → fix → retest:** Power/battery exhaustion → Recharge/power restore first → Separate newboot preflight.
- **Lesson/status:** Poweroffline is not C2/DDSsoftware regression; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only NONE.
- **Sources:** `onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md`.
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION; NONE.

#### HIST-048 — Nav2 package DNS install failure

- **Date / result / evidence:** 2026-09-26 / FAIL / HISTORICAL_DEPLOYMENT_REPORT.
- **Objective/configuration:** NETWORKING; ROSJazzy;packages.ros.org.
- **Execution/observation:** Couldnotresolvepackages.ros.org
- **Cause → fix → retest:** DNS/default-route failure → RestoreDNS beforeAPT → UNKNOWN.
- **Lesson/status:** Do not change package/distribution to mask DNS; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence FULLY. Direct NONE. Related only NONE.
- **Sources:** `onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md`.
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING BOTH; expected TEST_SESSION, FINDING; NONE.

#### HIST-049 — Publication flood and unbounded drain

- **Date / result / evidence:** 2026-09-27 / FAIL_THEN_PASS / OFFLINE_AND_LIVE_SOFTWARE_REPORT.
- **Objective/configuration:** ODOMETRY; SoleUDP43897;20mscallback.
- **Execution/observation:** ~154HzodomTFandcallbackstarvation bounded to<=50Hz
- **Cause → fix → retest:** Eachqueuedstate published;unbounddrain → Bounded64burst,newestonly → Live softwarevalidated.
- **Lesson/status:** Singleowner plus boundedwork preservefreshness; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence FULLY. Direct [FINDING-20260927-004](findings/FINDING-20260927-004-odom-publication-rate.md). Related only NONE.
- **Sources:** [ENGINEERING_KNOWLEDGE_BASE.md](../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- **Remaining gap:** MISSING BOTH; Recover existing IDs FINDING-20260927-004. Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [FINDING-20260927-004](findings/FINDING-20260927-004-odom-publication-rate.md), [TEST-20261002-027](tests/TEST-20261002-027-bounded-product-odometry-publication-repair.md).

#### HIST-050 — Nav2 AUTONOMY QoS stall

- **Date / result / evidence:** 2026-09-27 / FAIL_THEN_PASS / OFFLINE_AND_LIVE_SOFTWARE_REPORT.
- **Objective/configuration:** ROS2; Finitecaps,.300swatchdog.
- **Execution/observation:** CompatibleBEST_EFFORT/sensordata restored intentpath
- **Cause → fix → retest:** QoSincompatibility → CompatibleQoS → Focusedoffline/live softwarevalidated.
- **Lesson/status:** QoScompatibility separate fromprocesshealth; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence FULLY. Direct NONE. Related only [FINDING-20260930-001](findings/FINDING-20260930-001-command-authority.md).
- **Sources:** [ENGINEERING_KNOWLEDGE_BASE.md](../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [TEST-20261002-003](tests/TEST-20261002-003-autonomy-qos-stall-and-compatible-velocity-input.md), [FINDING-20261002-001](findings/FINDING-20261002-001-autonomy-velocity-qos-compatibility-preserves-independent-watchdog.md).

#### HIST-051 — Ghost source marker recovery

- **Date / result / evidence:** 2026-09-27 / PARTIAL / HISTORICAL_LIVE_SOFTWARE_REPORT.
- **Objective/configuration:** SAFETY; Arbiterlock/process/marker.
- **Execution/observation:** AUTONOMYmarkerblockednewacquisition;safezero/release restoredNONE
- **Cause → fix → retest:** Partialfailurecleanup marker divergence → Safeexisting-sourcecancel → Allsourceparity still open.
- **Lesson/status:** Marker is not authority; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING TEST SESSION; evidence FULLY. Direct [FINDING-20260930-001](findings/FINDING-20260930-001-command-authority.md). Related only NONE.
- **Sources:** [ENGINEERING_KNOWLEDGE_BASE.md](../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- **Remaining gap:** MISSING TEST SESSION; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [FINDING-20260930-001](findings/FINDING-20260930-001-command-authority.md), [TEST-20261002-011](tests/TEST-20261002-011-ghost-command-source-marker-safe-recovery.md), [FINDING-20261002-002](findings/FINDING-20261002-002-command-source-markers-do-not-establish-real-ownership.md).

#### HIST-052 — Dedicated highlevel posture temporary lease

- **Date / result / evidence:** 2026-09-27 / PARTIAL / HISTORICAL_PHYSICAL_REPORT.
- **Objective/configuration:** ROBOT_CONTROL; PersistentHIGHLEVEL;postureCLI.
- **Execution/observation:** Noplanar motion,sourceNONE;downpending
- **Cause → fix → retest:** Earlierlease/readiness failures; exact chainincomplete → Temporarylease/recovery separate lowlevel burst issue → Dedicateddown notclosed.
- **Lesson/status:** Do not conflate toggleA withstate-awareStand; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** PARTIALLY; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only [TEST-20260927-004](tests/TEST-20260927-004-laptop-xbox-manual.md).
- **Sources:** [TEST_CATALOG.md](../testing/TEST_CATALOG.md); [FAILURES_AND_FIXES.md](../FAILURES_AND_FIXES.md).
- **Remaining gap:** PARTIALLY; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Counting:** provenance alias; excluded from independent count.
- **Final coverage:** PARTIALLY; expected ; NONE.

#### HIST-053 — LiDAR mapping and TF physical history

- **Date / result / evidence:** 2026-09-27 / PARTIAL / HISTORICAL_PHYSICAL_REPORT.
- **Objective/configuration:** SENSORS; RPLIDAR;Home_Map;mapodom_base_lidar.
- **Execution/observation:** ~10Hzscan andacceptedchair;maphashes/extrinsicmetrology missing
- **Cause → fix → retest:** UNKNOWN → Single driver/TFownership → Product navigation observed separately.
- **Lesson/status:** Product use is not metrology/calibrationproof; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only [TEST-20260927-003](tests/TEST-20260927-003-home-map-localization.md).
- **Sources:** [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md); [TEST_CATALOG.md](../testing/TEST_CATALOG.md).
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20261002-017](tests/TEST-20261002-017-home-map-mapping-and-save-load-historical-operation.md).

#### HIST-054 — NavFn false footprint collision diagnostic

- **Date / result / evidence:** 2026-09-27 / FAIL_THEN_PASS / OFFLINE_PROVEN.
- **Objective/configuration:** NAVIGATION; Curvedpaths yaw0.
- **Execution/observation:** Yaw0 treatedbodyheading causedfalsecollision
- **Cause → fix → retest:** Bodyorientationassumedfromdefaultposeyaw → Path-tangentorientation → Curvedzero-yawregression/dryplanning.
- **Lesson/status:** Preserve scan/costmap/TF/fullfootprint forprecisionclearance; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence FULLY. Direct NONE. Related only [FINDING-20260927-003](findings/FINDING-20260927-003-obstacle-snapshot.md).
- **Sources:** [ENGINEERING_KNOWLEDGE_BASE.md](../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [TEST-20261002-012](tests/TEST-20261002-012-navfn-path-tangent-clearance-correction.md), [FINDING-20261002-006](findings/FINDING-20261002-006-zero-yaw-navfn-poses-need-path-tangent-footprint-diagnostics.md).

#### HIST-055 — Headless and D455 ondemand resource snapshot

- **Date / result / evidence:** 2026-09-27 / PASS_STATIC / LIVE_STATIC_REPORT.
- **Objective/configuration:** PERFORMANCE; RVizlaptop;D455notusedbyDay2Nav2.
- **Execution/observation:** Load9.02/7.69/5.11→1.33/1.08/.56;RAM~1.7→1GiB;camera~98percentcore→0
- **Cause → fix → retest:** UnneededrobotGUI/cameraworkload → Headless/on-demandcamera → No sustainedheadroomsoak.
- **Lesson/status:** D455driverpresence is notNav2/perception/extrinsicproof; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence FULLY. Direct NONE. Related only [FINDING-20260927-002](findings/FINDING-20260927-002-rtl8851bu.md).
- **Sources:** [PERFORMANCE_BASELINE.md](../operations/PERFORMANCE_BASELINE.md).
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [TEST-20261002-007](tests/TEST-20261002-007-headless-mini-pc-and-on-demand-workload-snapshots.md), [FINDING-20261002-007](findings/FINDING-20261002-007-on-demand-unused-perception-reduced-recorded-mini-pc-load.md).

#### HIST-056 — Obstacle snapshot tool and packaging

- **Date / result / evidence:** 2026-09-28 / FAIL_THEN_OFFLINE_PASS / OFFLINE_PROVEN.
- **Objective/configuration:** NAVIGATION; Boundedsnapshot;sessionoverride70percentx3<=180s.
- **Execution/observation:** 8mmhistoricalclearancenonreconstructable;renamedexecnotimportable
- **Cause → fix → retest:** Missingjointartifacts;CMakeextensionlessonly → Storefullsnapshot;install.pyandexec → Packagingregression;liveinstalledbundlepending.
- **Lesson/status:** Override never changesnormal80percentgate; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING TEST SESSION; evidence FULLY. Direct [FINDING-20260927-003](findings/FINDING-20260927-003-obstacle-snapshot.md). Related only NONE.
- **Sources:** [ENGINEERING_KNOWLEDGE_BASE.md](../operations/ENGINEERING_KNOWLEDGE_BASE.md); `git7ae1688,4a95852`.
- **Remaining gap:** MISSING TEST SESSION; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [FINDING-20260927-003](findings/FINDING-20260927-003-obstacle-snapshot.md), [TEST-20261002-006](tests/TEST-20261002-006-importable-obstacle-helper-packaging-repair.md), [TEST-20261002-018](tests/TEST-20261002-018-reconstructable-obstacle-snapshot-software-repair.md), [FINDING-20261002-003](findings/FINDING-20261002-003-installed-executable-helpers-also-need-an-importable-module.md).
- **Supplemental scope:** 8mm clearance could not be reconstructed: audit-failure: Missing combinedscan/costmaps/TF/candidates/limitingposecell.; tool-fix: Boundedsnapshot format capturesinputs/perpose/source; offline regression.; installed-validation: Nextlive obstacle test must confirm retained installedartifactset..

#### HIST-057 — Wrongmap confidence investigation

- **Date / result / evidence:** 2026-09-28 / FAIL_THEN_OFFLINE_FIX / HISTORICAL_REPORT_AND_SOURCE.
- **Objective/configuration:** LOCALIZATION; OldHome_Map atnewsite.
- **Execution/observation:** Mapidentitywrong;nojustificationtotuneextrinsicsAMCLororigin
- **Cause → fix → retest:** Active map identity insufficientlyvisible → Display/preserveactiveYAML → Liveintendedmapdeploymentverificationqualified.
- **Lesson/status:** Checkmapbefore thresholds; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING TEST SESSION; evidence FULLY. Direct [FINDING-20260928-001](findings/FINDING-20260928-001-active-map-identity.md). Related only NONE.
- **Sources:** [ENGINEERING_KNOWLEDGE_BASE.md](../operations/ENGINEERING_KNOWLEDGE_BASE.md); `FINDING-20260928-001`.
- **Remaining gap:** MISSING TEST SESSION; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [FINDING-20260928-001](findings/FINDING-20260928-001-active-map-identity.md), [TEST-20261002-010](tests/TEST-20261002-010-wrong-map-localization-and-active-map-preflight-repair.md).

#### HIST-061 — rtl8851bu network instability remains open

- **Date / result / evidence:** 2026-09-27 / KNOWN_ISSUE / ENGINEERING_FINDING_REPORT.
- **Objective/configuration:** NETWORKING, MINI_PC, RELIABILITY; See source.
- **Execution/observation:** Kernel evidence included out-of-tree `rtl8851bu` UBSAN array-index errors and concurrent station/AP-style interfaces during intermittent network loss. A policy to pin NetworkManager, disable Wi-Fi power saving, and preserve the station address was prepared, but long-soak closure is absent. - Evidence: Day-2 closeout and operations KB. - Impact: Mini-PC can appear unreachable while Linux crash evidence is absent. - Current status: partial mitigation; long network/reboot/mission-load soak remains required. - DO NOT REPEAT: attribute every SSH loss to this driver; resource starvation and bridge/address faults have separate evidence.
- **Cause → fix → retest:** See retained finding → See retained finding → See retained finding.
- **Lesson/status:** Preserve separate incident and evidence limitation; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING TEST SESSION; evidence EVIDENCE INCOMPLETE. Direct [FINDING-20260927-002](findings/FINDING-20260927-002-rtl8851bu.md). Related only NONE.
- **Sources:** [FINDING-20260927-002-rtl8851bu.md](findings/FINDING-20260927-002-rtl8851bu.md) @173f61d.
- **Remaining gap:** MISSING TEST SESSION; Existing HEAD finding.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [FINDING-20260927-002](findings/FINDING-20260927-002-rtl8851bu.md), [TEST-20261002-009](tests/TEST-20261002-009-network-loss-diagnosis-and-prepared-rtl8851bu-mitigation.md).

### Sep29–Oct1


#### HIST-018 — Relocalize approval and cancellation safety

- **Date / result / evidence:** 2026-09-29 / PASS / OFFLINE_PROVEN.
- **Objective/configuration:** LOCALIZATION, SAFETY, ROBOT_CONTROL; SHA b98a1af; robot robot_01.
- **Execution/observation:** Focused offline tests verify read-only status, default-no approval, explicit approval gating, deterministic/idempotent cancellation, zero/release cleanup, and the `>=80%` ×3 success condition. No physical relocalization is claimed.
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING FINDING; evidence FULLY. Direct [TEST-20260929-001](tests/TEST-20260929-001-relocalize-approval.md). Related only NONE.
- **Sources:** [TEST-20260929-001-relocalize-approval.md](tests/TEST-20260929-001-relocalize-approval.md) @173f61d.
- **Remaining gap:** MISSING FINDING; Existing record at HEAD.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20260929-001](tests/TEST-20260929-001-relocalize-approval.md).

#### HIST-019 — NOMAD Phase-1 vendor-neutral read-only status

- **Date / result / evidence:** 2026-09-30 / PASS / OFFLINE_PROVEN.
- **Objective/configuration:** NOMAD, MQTT, SAFETY; SHA d8ede0a; robot robodog_01.
- **Execution/observation:** The versioned platform-status contract, MQTT ingestion, FleetRegistry/UI presentation, stale/offline fail-closed behavior, multi-robot isolation, and absence of motion surfaces were validated offline on NOMAD branch `raz/bipolix-integration`.
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING FINDING; evidence FULLY. Direct [TEST-20260930-001](tests/TEST-20260930-001-nomad-phase1-status.md). Related only NONE.
- **Sources:** [TEST-20260930-001-nomad-phase1-status.md](tests/TEST-20260930-001-nomad-phase1-status.md) @173f61d.
- **Remaining gap:** MISSING FINDING; Existing record at HEAD.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20260930-001](tests/TEST-20260930-001-nomad-phase1-status.md).

#### HIST-020 — NOMAD Phase-2 remote-authority reservation

- **Date / result / evidence:** 2026-09-30 / PASS / OFFLINE_PROVEN.
- **Objective/configuration:** NOMAD, MQTT, SAFETY, XBOX; SHA fa6810e; robot robodog_01.
- **Execution/observation:** Offline tests covered ACQUIRE/RENEW/RELEASE, TTL, generation/session identity, replay/idempotency, conflicts, disconnect cleanup, safe robot switching, and multi-robot isolation. NOMAD operator lease, remote reservation, and actual `COMMAND_SOURCE` remained separate; reservation did not acquire robot motion.
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING FINDING; evidence FULLY. Direct [TEST-20260930-002](tests/TEST-20260930-002-nomad-phase2-authority.md). Related only NONE.
- **Sources:** [TEST-20260930-002-nomad-phase2-authority.md](tests/TEST-20260930-002-nomad-phase2-authority.md) @173f61d.
- **Remaining gap:** MISSING FINDING; Existing record at HEAD.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20260930-002](tests/TEST-20260930-002-nomad-phase2-authority.md).

#### HIST-021 — NOMAD Phase-3A mock TeleopIntent pipeline

- **Date / result / evidence:** 2026-09-30 / PASS / OFFLINE_PROVEN.
- **Objective/configuration:** NOMAD, MQTT, XBOX, SAFETY; SHA 4561e74; robot robodog_01.
- **Execution/observation:** The production-shaped MQTT contract was validated against a deterministic mock receiver for authority, epoch, sequence, freshness, deadman, neutral gate, watchdog, malformed values, reconnect/switch cleanup, and multi-robot isolation. It recorded intent only.
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING FINDING; evidence FULLY. Direct [TEST-20260930-003](tests/TEST-20260930-003-nomad-phase3a-mock.md). Related only NONE.
- **Sources:** [TEST-20260930-003-nomad-phase3a-mock.md](tests/TEST-20260930-003-nomad-phase3a-mock.md) @173f61d.
- **Remaining gap:** MISSING FINDING; Existing record at HEAD.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20260930-003](tests/TEST-20260930-003-nomad-phase3a-mock.md).

#### HIST-022 — NOMAD Phase-3B real Mini-PC non-motion integration

- **Date / result / evidence:** 2026-10-01 / PASS / LIVE_STATIC_PROVEN.
- **Objective/configuration:** NOMAD, MQTT, MINI_PC, SAFETY; SHA a0cda36; robot robodog_01.
- **Execution/observation:** The real Mini-PC exporter/gateway-only profile and edge broker were observed through the real MQTT path. With robot telemetry unavailable, authority, drive-shaped intent, Mission, and Patrol correctly failed closed; velocity remained zero, physical output false, `COMMAND_SOURCE=NONE`, and owner lock absent.
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING FINDING; evidence FULLY. Direct [TEST-20261001-001](tests/TEST-20261001-001-nomad-phase3b-live-static.md). Related only NONE.
- **Sources:** [TEST-20261001-001-nomad-phase3b-live-static.md](tests/TEST-20261001-001-nomad-phase3b-live-static.md) @173f61d.
- **Remaining gap:** MISSING FINDING; Existing record at HEAD.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20261001-001](tests/TEST-20261001-001-nomad-phase3b-live-static.md).

#### HIST-023 — First bounded NOMAD Phase-3C Xbox forward and stop

- **Date / result / evidence:** 2026-10-01 / PLANNED / PLANNED.
- **Objective/configuration:** XBOX, NOMAD, MQTT, ROBOT_CONTROL, SAFETY; SHA UNKNOWN; robot robodog_01.
- **Execution/observation:** UNKNOWN
- **Cause → fix → retest:** See source; UNKNOWN unless explicitly stated → See source; no inferred fix → See source; only declared result.
- **Lesson/status:** Evidence class remains configuration bounded; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING FINDING; evidence PARTIALLY. Direct [TEST-20261001-002](tests/TEST-20261001-002-phase3c-xbox-physical.md). Related only NONE.
- **Sources:** [TEST-20261001-002-phase3c-xbox-physical.md](tests/TEST-20261001-002-phase3c-xbox-physical.md) @173f61d.
- **Remaining gap:** MISSING FINDING; Existing record at HEAD.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20261001-002](tests/TEST-20261001-002-phase3c-xbox-physical.md).

#### HIST-058 — Git versus deployed consumer reconciliation

- **Date / result / evidence:** 2026-09-29 / PASS_RECONCILIATION / COMMITTED_READ_ONLY_AUDIT.
- **Objective/configuration:** DEPLOYMENT; b98a1af;contenthashcomparison.
- **Execution/observation:** InstalledLiDARmatchedGitwhilesourcesstale;hybridtree;180soverenvelopepreserved
- **Cause → fix → retest:** Source/deployeddrift → Reconcilebyactualconsumers;excludeinstallbuildlogorig → Relocalizeofflinetests;no deploymentbythisaudit.
- **Lesson/status:** No singlecopiedtree authoritative; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING TEST SESSION; evidence FULLY. Direct [FINDING-20260929-001](findings/FINDING-20260929-001-source-of-truth.md). Related only NONE.
- **Sources:** [SOURCE_OF_TRUTH_RECONCILIATION_2026-09-29.md](../architecture/SOURCE_OF_TRUTH_RECONCILIATION_2026-09-29.md).
- **Remaining gap:** MISSING TEST SESSION; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** FULLY; expected FINDING; [FINDING-20260929-001](findings/FINDING-20260929-001-source-of-truth.md).
- **Supplemental scope:** Override explicit70%x3,180s bound versus stale10min doc: reconcile: Independenttokenproducer+consumer180s; normal80%x3unchanged.; documentation-drift: OBSTACLE_TEST stillsays atmosttenminutes..

#### HIST-062 — Timed-out platform-status probes leaked ROS child processes

- **Date / result / evidence:** 2026-10-01 / RESOLVED / ENGINEERING_FINDING_REPORT.
- **Objective/configuration:** PERFORMANCE, RELIABILITY, MINI_PC, ROS2; See source.
- **Execution/observation:** Ping could remain responsive while SSH banner/service responsiveness degraded. The old exporter timed out short ROS CLI probes without reliably terminating and reaping their process groups, causing child/task/memory growth. Commit `e396f55` adds process-group termination/reaping and regression coverage. - Evidence: commit `e396f55`, platform exporter architecture, and performance baseline. - Root cause: resource exhaustion from accumulating probes, not proof of a Wi-Fi driver failure. - Known good: bounded probe lifecycle; distinguish brief probe spikes from monotonic growth. - Validation limitation: exact soak metrics referenced during the incident are not retained as a… [full details in JSON]
- **Cause → fix → retest:** See retained finding → See retained finding → See retained finding.
- **Lesson/status:** Preserve separate incident and evidence limitation; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING TEST SESSION; evidence FULLY. Direct [FINDING-20261001-001](findings/FINDING-20261001-001-exporter-process-leak.md). Related only NONE.
- **Sources:** [FINDING-20261001-001-exporter-process-leak.md](findings/FINDING-20261001-001-exporter-process-leak.md) @173f61d.
- **Remaining gap:** MISSING TEST SESSION; Existing HEAD finding.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [FINDING-20261001-001](findings/FINDING-20261001-001-exporter-process-leak.md), [TEST-20261002-008](tests/TEST-20261002-008-exporter-timeout-process-group-cleanup.md).

#### HIST-063 — Stale central-broker address stopped live platform status

- **Date / result / evidence:** 2026-10-01 / RESOLVED / ENGINEERING_FINDING_REPORT.
- **Objective/configuration:** MQTT, NETWORKING, NOMAD, DEPLOYMENT; See source.
- **Execution/observation:** The Mini-PC/edge path was running, but the bridge targeted the former laptop address `192.168.2.142` instead of the active C&C address `192.168.2.177`. Updating the bridge destination restored topic arrival/FleetRegistry visibility. - Evidence: Phase-3B plan records the `.177` update; the exact incident log is `EVIDENCE MISSING`. - DO NOT REPEAT: diagnose `never_seen` as robot readiness before tracing edge publish → bridge destination → central broker → registry ingestion. - Deployment lesson: broker host is configuration, never a stale copied development-host constant.
- **Cause → fix → retest:** See retained finding → See retained finding → See retained finding.
- **Lesson/status:** Preserve separate incident and evidence limitation; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING TEST SESSION; evidence FULLY. Direct [FINDING-20261001-002](findings/FINDING-20261001-002-mqtt-bridge-ip.md). Related only NONE.
- **Sources:** [FINDING-20261001-002-mqtt-bridge-ip.md](findings/FINDING-20261001-002-mqtt-bridge-ip.md) @173f61d.
- **Remaining gap:** MISSING TEST SESSION; Existing HEAD finding.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [FINDING-20261001-002](findings/FINDING-20261001-002-mqtt-bridge-ip.md), [TEST-20261002-032](tests/TEST-20261002-032-stale-central-mqtt-bridge-destination-incident.md).

#### HIST-064 — Linux joystick presence does not imply Firefox Gamepad visibility

- **Date / result / evidence:** 2026-10-01 / CURRENT / ENGINEERING_FINDING_REPORT.
- **Objective/configuration:** XBOX, NOMAD, SAFETY; See source.
- **Execution/observation:** `/dev/input/js0` proved Linux input availability, not browser exposure. Firefox required a focused page/user controller interaction and robust handling of `gamepadconnected` plus polling; strict assumptions about a `standard` mapping could leave the UI `DISCONNECTED` despite the device existing. - Evidence: current NOMAD Phase-3C UI source/tests in RobotConsolePage.vue and AuthorityPanel.vue. - Live historical observation: UI later displayed `CONNECTED`, neutral, axes, and RB. A committed screenshot/log reference is `EVIDENCE MISSING`, so this finding does not itself promote the upcoming physical test. - DO NOT REPEAT: equate `/dev/input/js0` with Gamepad API readiness… [full details in JSON]
- **Cause → fix → retest:** See retained finding → See retained finding → See retained finding.
- **Lesson/status:** Preserve separate incident and evidence limitation; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING TEST SESSION; evidence FULLY. Direct [FINDING-20261001-003](findings/FINDING-20261001-003-firefox-gamepad.md). Related only NONE.
- **Sources:** [FINDING-20261001-003-firefox-gamepad.md](findings/FINDING-20261001-003-firefox-gamepad.md) @173f61d.
- **Remaining gap:** MISSING TEST SESSION; Existing HEAD finding.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [FINDING-20261001-003](findings/FINDING-20261001-003-firefox-gamepad.md), [TEST-20261002-031](tests/TEST-20261002-031-firefox-gamepad-visibility-failure-and-reported-ui-recovery.md).

#### HIST-065 — Vendor basic-state 98 is valid non-fault telemetry

- **Date / result / evidence:** 2026-10-01 / CURRENT / ENGINEERING_FINDING_REPORT.
- **Objective/configuration:** ROBOT_CONTROL, SAFETY, NOMAD; See source.
- **Execution/observation:** Vendor basic-state value `98` is a valid, non-fault state and must not make platform telemetry unhealthy. It is also not, by itself, authoritative proof that the robot is `STANDING`; drive remains blocked until the separate fresh posture/readiness mechanism confirms standing. - Evidence: NOMAD Phase-3C design and current Lite-robot exporter/watchdog source. The associated Lite changes are present in the current working tree and are not yet claimed as committed deployment evidence. - Known good: report 98 as valid telemetry, preserve posture as unknown/not standing until independently confirmed. - DO NOT REPEAT: label 98 a fault, change its vendor mapping, or silently map… [full details in JSON]
- **Cause → fix → retest:** See retained finding → See retained finding → See retained finding.
- **Lesson/status:** Preserve separate incident and evidence limitation; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING TEST SESSION; evidence FULLY. Direct [FINDING-20261001-004](findings/FINDING-20261001-004-vendor-state-98.md). Related only NONE.
- **Sources:** [FINDING-20261001-004-vendor-state-98.md](findings/FINDING-20261001-004-vendor-state-98.md) @173f61d.
- **Remaining gap:** MISSING TEST SESSION; Existing HEAD finding.
- **Final coverage:** FULLY; expected FINDING; [FINDING-20261001-004](findings/FINDING-20261001-004-vendor-state-98.md).

#### HIST-090 — Nav2 CPU SIGILL and RPP fallback

- **Date / result / evidence:** 2026-10-01 / FAIL → fix present; physical retest UNKNOWN / LIVE_STATIC_PROVEN current audit; HISTORICAL_CLAIM historical field failures.
- **Objective/configuration:** DEPLOYMENT, SAFETY, EVIDENCE; Mini-PC tracked-clean main b4f6a48; current laptop bipolix_robot0c48b4d; read-only capture2026-10-02.
- **Execution/observation:** Nav2 CPU SIGILL and RPP fallback; see exact source facts and limitations in deployed-state audit.
- **Cause → fix → retest:** MPPI binary AVX instructions on CPU without AVX, reported by Git141b497 → CPU-aware RPP selection/dependency deployed; not integrated locally → Fix presence verified by read-only source/deployment audit where stated; no physical retest executed, historical physical retest UNKNOWN..
- **Lesson/status:** Deployment and source identity are readiness prerequisites; no automatic inheritance of historical physical proof; CURRENT reconciliation/evidence gap.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE for physical retest/raw history. Direct NONE. Related only NONE.
- **Sources:** [MINIPC_DEPLOYED_STATE_AUDIT.md](MINIPC_DEPLOYED_STATE_AUDIT.md); [MINIPC_READ_ONLY_20261002.json](evidence/MINIPC_READ_ONLY_20261002.json); `NOMAD git141b497`.
- **Remaining gap:** Physical retest/deployment reconciliation remains open; scope details in source audit.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [FINDING-20261002-080](findings/FINDING-20261002-080-nav2-cpu-compatibility-fix-exists-deployed-but-not-on-integratio.md), [TEST-20261002-080](tests/TEST-20261002-080-minipc-read-only-evidence-audit.md).

### current integration


#### HIST-060 — Current existing-path Lite3 integration

- **Date / result / evidence:** 2026-10-02 / PASS_OFFLINE_ONLY / OFFLINE_PROVEN.
- **Objective/configuration:** NOMAD; Cbranchbipolix_robot;c6461cc,fb4191d,a88f7be,dd817e9.
- **Execution/observation:** Offlineintegrationtested;currentcompletephysicalpathneveraccepted
- **Cause → fix → retest:** Reviewcaughtkeyboardbubbling/stalecancelraces;fixed → Ownership/neutralfences andgeneration-awarecancel → Frontend1064pass;backend5382pass30skip4failthenaffectedreruns;noallgreenbroadclaim.
- **Lesson/status:** SI-labelledrequestnotmeasuredspeed;newpathneedsphysicalacceptance; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence PARTIALLY. Direct NONE. Related only [TEST-20261001-002](tests/TEST-20261001-002-phase3c-xbox-physical.md).
- **Sources:** [LITE3_INTEGRATION.md](../../../../Documents/NOMAD/docs/LITE3_INTEGRATION.md).
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION; NONE.

#### HIST-091 — Stationary Auto telemetry odometry drift

- **Date / result / evidence:** 2026-10-02 / FAIL → fix present; physical retest UNKNOWN / LIVE_STATIC_PROVEN current audit; HISTORICAL_CLAIM historical field failures.
- **Objective/configuration:** DEPLOYMENT, SAFETY, EVIDENCE; Mini-PC tracked-clean main b4f6a48; current laptop bipolix_robot0c48b4d; read-only capture2026-10-02.
- **Execution/observation:** Stationary Auto telemetry odometry drift; see exact source facts and limitations in deployed-state audit.
- **Cause → fix → retest:** Reported stepping-in-place telemetry integrated by EKF/SLAM, Gitb4f6a48 → Command-intent stillness suppression0.5s deployed; handheld bypass caveat → Fix presence verified by read-only source/deployment audit where stated; no physical retest executed, historical physical retest UNKNOWN..
- **Lesson/status:** Deployment and source identity are readiness prerequisites; no automatic inheritance of historical physical proof; CURRENT reconciliation/evidence gap.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE for physical retest/raw history. Direct NONE. Related only NONE.
- **Sources:** [MINIPC_DEPLOYED_STATE_AUDIT.md](MINIPC_DEPLOYED_STATE_AUDIT.md); [MINIPC_READ_ONLY_20261002.json](evidence/MINIPC_READ_ONLY_20261002.json); `NOMAD gitb4f6a48`.
- **Remaining gap:** Physical retest/deployment reconciliation remains open; scope details in source audit.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [FINDING-20261002-081](findings/FINDING-20261002-081-idle-odometry-fix-exists-deployed-but-not-on-integration-branch.md), [TEST-20261002-080](tests/TEST-20261002-080-minipc-read-only-evidence-audit.md).

#### HIST-092 — Installed authority/configuration differs from integration

- **Date / result / evidence:** 2026-10-02 / PARTIAL / LIVE_STATIC_PROVEN current audit; HISTORICAL_CLAIM historical field failures.
- **Objective/configuration:** DEPLOYMENT, SAFETY, EVIDENCE; Mini-PC tracked-clean main b4f6a48; current laptop bipolix_robot0c48b4d; read-only capture2026-10-02.
- **Execution/observation:** Installed authority/configuration differs from integration; see exact source facts and limitations in deployed-state audit.
- **Cause → fix → retest:** Branch/config divergence; higher caps and altered odom sign rationale UNKNOWN → Documentation/findings; no deployment or configuration modification → Fix presence verified by read-only source/deployment audit where stated; no physical retest executed, historical physical retest UNKNOWN..
- **Lesson/status:** Deployment and source identity are readiness prerequisites; no automatic inheritance of historical physical proof; CURRENT reconciliation/evidence gap.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE for physical retest/raw history. Direct NONE. Related only NONE.
- **Sources:** [MINIPC_DEPLOYED_STATE_AUDIT.md](MINIPC_DEPLOYED_STATE_AUDIT.md); [MINIPC_READ_ONLY_20261002.json](evidence/MINIPC_READ_ONLY_20261002.json).
- **Remaining gap:** Physical retest/deployment reconciliation remains open; scope details in source audit.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [FINDING-20261002-082](findings/FINDING-20261002-082-deployed-control-guards-and-site-configuration-differ-from-integ.md), [TEST-20261002-080](tests/TEST-20261002-080-minipc-read-only-evidence-audit.md).

#### HIST-093 — Legacy status exporter differs from product ROS domain

- **Date / result / evidence:** 2026-10-02 / PARTIAL / LIVE_STATIC_PROVEN current audit; HISTORICAL_CLAIM historical field failures.
- **Objective/configuration:** DEPLOYMENT, SAFETY, EVIDENCE; Mini-PC tracked-clean main b4f6a48; current laptop bipolix_robot0c48b4d; read-only capture2026-10-02.
- **Execution/observation:** Legacy status exporter differs from product ROS domain; see exact source facts and limitations in deployed-state audit.
- **Cause → fix → retest:** Observed domain0 versus23; sole cause of OFFLINE UNKNOWN → No repair performed; authoritative product state required → Fix presence verified by read-only source/deployment audit where stated; no physical retest executed, historical physical retest UNKNOWN..
- **Lesson/status:** Deployment and source identity are readiness prerequisites; no automatic inheritance of historical physical proof; CURRENT reconciliation/evidence gap.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE for physical retest/raw history. Direct NONE. Related only NONE.
- **Sources:** [MINIPC_DEPLOYED_STATE_AUDIT.md](MINIPC_DEPLOYED_STATE_AUDIT.md); [MINIPC_READ_ONLY_20261002.json](evidence/MINIPC_READ_ONLY_20261002.json).
- **Remaining gap:** Physical retest/deployment reconciliation remains open; scope details in source audit.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [FINDING-20261002-083](findings/FINDING-20261002-083-legacy-status-domain-and-advertised-capabilities-are-not-product.md), [TEST-20261002-080](tests/TEST-20261002-080-minipc-read-only-evidence-audit.md).

#### HIST-094 — Retained bags and clock provenance limits

- **Date / result / evidence:** 2026-10-02 / PARTIAL / LIVE_STATIC_PROVEN current audit; HISTORICAL_CLAIM historical field failures.
- **Objective/configuration:** DEPLOYMENT, SAFETY, EVIDENCE; Mini-PC tracked-clean main b4f6a48; current laptop bipolix_robot0c48b4d; read-only capture2026-10-02.
- **Execution/observation:** Retained bags and clock provenance limits; see exact source facts and limitations in deployed-state audit.
- **Cause → fix → retest:** September15 referenced bag payloads absent; service clock mismatch cause UNKNOWN → Preserve explicit evidence gaps; no replay or recovery performed → Fix presence verified by read-only source/deployment audit where stated; no physical retest executed, historical physical retest UNKNOWN..
- **Lesson/status:** Deployment and source identity are readiness prerequisites; no automatic inheritance of historical physical proof; CURRENT reconciliation/evidence gap.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE for physical retest/raw history. Direct NONE. Related only NONE.
- **Sources:** [MINIPC_DEPLOYED_STATE_AUDIT.md](MINIPC_DEPLOYED_STATE_AUDIT.md); [MINIPC_READ_ONLY_20261002.json](evidence/MINIPC_READ_ONLY_20261002.json).
- **Remaining gap:** Physical retest/deployment reconciliation remains open; scope details in source audit.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [FINDING-20261002-084](findings/FINDING-20261002-084-retained-bags-and-clock-metadata-impose-evidence-limits.md), [TEST-20261002-080](tests/TEST-20261002-080-minipc-read-only-evidence-audit.md).

### UNKNOWN date


#### HIST-025 — Acquisition-only request/release

- **Date / result / evidence:** UNKNOWN / PARTIAL / HISTORICAL_OPERATOR_REPORT.
- **Objective/configuration:** MOTIONSDK; Historical dirty base c243294; ControlGet(2) request; ControlGet(1) release; Start receive-only; no RobotStateInit.
- **Execution/observation:** Stillness reported; REQUEST_SENT/OWNERSHIP_UNCONFIRMED; gate0
- **Cause → fix → retest:** SDK supplies no ownership acknowledgement → Request remains separate from acknowledgement → E5 after normal lying; no motion.
- **Lesson/status:** Never promote request to confirmed control; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct [FINDING-20260913-001](findings/FINDING-20260913-001-motion-sdk-ownership-unconfirmed.md). Related only NONE.
- **Sources:** [EXPERIMENTS.md](../EXPERIMENTS.md); [ACQUISITION_ONLY_SAFETY_REVIEW.md](../ACQUISITION_ONLY_SAFETY_REVIEW.md); [DECISIONS.md](../DECISIONS.md).
- **Remaining gap:** MISSING BOTH; Recover existing IDs FINDING-20260913-001. Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** FULLY; expected FINDING; [FINDING-20260913-001](findings/FINDING-20260913-001-motion-sdk-ownership-unconfirmed.md).

#### HIST-039 — Retained 72 jointscale sweep

- **Date / result / evidence:** UNKNOWN / FAIL / LOCAL_SIMULATION_ARTIFACTS.
- **Objective/configuration:** R_AND_D; artifacts/joint_leg_lift_sweep; date UNKNOWN.
- **Execution/observation:** 0completed/72;unload not achieved in retained results
- **Cause → fix → retest:** Contact/gain/control family limitations; hardware cause UNKNOWN → Later calibrated robust campaign → Robust campaign also no unload.
- **Lesson/status:** Preserve failed local artifacts; dates cannot derive from mtime; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence PARTIALLY. Direct NONE. Related only [TEST-20260921-001](tests/TEST-20260921-001-fr-robust-unload-campaign.md), [FINDING-20260921-001](findings/FINDING-20260921-001-simulation-contact-model-ambiguity.md).
- **Sources:** [results.csv](../../artifacts/joint_leg_lift_sweep/results.csv).
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION; NONE.

#### HIST-040 — Retained 180 thigh-knee angle sweep

- **Date / result / evidence:** UNKNOWN / FAIL / LOCAL_SIMULATION_ARTIFACTS.
- **Objective/configuration:** R_AND_D; artifacts/joint_angle_sweep; date UNKNOWN.
- **Execution/observation:** 0completed/180;FR not unloaded
- **Cause → fix → retest:** Model family limitation; physical cause UNKNOWN → Robust force/contactaudit later → No hardware inference.
- **Lesson/status:** Joint scaling is not Cartesian scaling; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence PARTIALLY. Direct NONE. Related only [TEST-20260921-001](tests/TEST-20260921-001-fr-robust-unload-campaign.md), [FINDING-20260921-001](findings/FINDING-20260921-001-simulation-contact-model-ambiguity.md).
- **Sources:** [results.csv](../../artifacts/joint_angle_sweep/results.csv).
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION; NONE.

#### HIST-041 — Retained 79 Cartesian lift sweep

- **Date / result / evidence:** UNKNOWN / FAIL / LOCAL_SIMULATION_ARTIFACTS.
- **Objective/configuration:** R_AND_D; artifacts/leg_lift_sweep;dateUNKNOWN.
- **Execution/observation:** 0completed/79
- **Cause → fix → retest:** Threshold failure in modeled family → Subsequent grid/robust work → Different gains/families not comparable.
- **Lesson/status:** No successful physical clearance follows from simulation; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence PARTIALLY. Direct NONE. Related only [TEST-20260921-001](tests/TEST-20260921-001-fr-robust-unload-campaign.md), [FINDING-20260921-001](findings/FINDING-20260921-001-simulation-contact-model-ambiguity.md).
- **Sources:** [results.csv](../../artifacts/leg_lift_sweep/results.csv).
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION; NONE.

#### HIST-042 — Retained grid162 and sensitivity

- **Date / result / evidence:** UNKNOWN / PASS_LOCAL_MODEL_ONLY / LOCAL_SIMULATION_ARTIFACTS.
- **Objective/configuration:** R_AND_D; PD140/180/220-class highergain simulation; varied friction/timing.
- **Execution/observation:** 147declared pass/15fail in local CSV; excludes current physical guard equivalence
- **Cause → fix → retest:** Declared synthetic thresholds/gains differ from physical limits → Later robustbounded campaign → Zero robustunload later.
- **Lesson/status:** A local pass is config-bound; never product/hardware capability; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence PARTIALLY. Direct NONE. Related only [TEST-20260921-001](tests/TEST-20260921-001-fr-robust-unload-campaign.md), [FINDING-20260921-001](findings/FINDING-20260921-001-simulation-contact-model-ambiguity.md).
- **Sources:** [results.csv](../../artifacts/grid_162/results.csv); `artifacts/single_leg_sensitivity`.
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION; NONE.

#### HIST-043 — Retained newplan FR failure

- **Date / result / evidence:** UNKNOWN / FAIL / LOCAL_SIMULATION_ARTIFACTS.
- **Objective/configuration:** R_AND_D; MuJoCo2.3.7;metadata mixed PD180/3.5 and newplan60/.7.
- **Execution/observation:** .4388mmclearance,zero unload;maxrate1.6994rad/s
- **Cause → fix → retest:** Model/config boundary and inadequate clearance → No proven fix → Robust campaign later.
- **Lesson/status:** Preserve parameter metadata inconsistency rather than flattening; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence PARTIALLY. Direct NONE. Related only [TEST-20260921-001](tests/TEST-20260921-001-fr-robust-unload-campaign.md), [FINDING-20260921-001](findings/FINDING-20260921-001-simulation-contact-model-ambiguity.md).
- **Sources:** [summary.json](../../artifacts/one_leg_lift_newplan/summary.json).
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION; NONE.

#### HIST-044 — Body-only 30/60/90 percent safe-scale calibration plan

- **Date / result / evidence:** UNKNOWN / IMPLEMENTED; PHYSICAL RESULT UNKNOWN / COMMITTED_SOURCE.
- **Objective/configuration:** ROBOT_CONTROL; Cartesian body reference (-0.029043,+0.026558,0)m; 0.30/0.60/0.90 fractions of computed joint-limit safe scale; keep all nominal foot heights.
- **Execution/observation:** Source establishes plan and numerous refinement modes, not hardware PASS. Physical ForceOpt slowdown comments reference late contact/PD settling transient but no primary local run trace identified.
- **Cause → fix → retest:** UNKNOWN → NONE → UNKNOWN.
- **Lesson/status:** 30/60/90 safe fractions are different from the later proposed 25/50/75 model-validation plan; source names do not prove a run; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence PARTIALLY. Direct NONE. Related only [TEST-20260918-001](tests/TEST-20260918-001-body-shift-progression.md).
- **Sources:** [supported_body_shift_plan.hpp](../../state_machine/supported_body_shift_plan.hpp); [supported_body_shift_plan_test.cpp](../../tests/supported_body_shift_plan_test.cpp); [supported_body_shift_once_test.cpp](../../tests/supported_body_shift_once_test.cpp).
- **Remaining gap:** MISSING BOTH; Missing each level physical timestamp, target/actual trace, guards and outcome.
- **Final coverage:** MISSING FINDING; expected FINDING; NONE.

#### HIST-059 — Prior directNOMADstrafe failure

- **Date / result / evidence:** UNKNOWN / FAIL / USER_REPORTED.
- **Objective/configuration:** NOMAD; Date/path/SHA/mode/rawaxesUNKNOWN.
- **Execution/observation:** DirectstrafehasnoPASS;oldROSy0notdirectfailurediagnosis
- **Cause → fix → retest:** UNKNOWN → No verifiedfix → Currentphysicalstrafeunvalidated.
- **Lesson/status:** Neverinventsign/scaling/gaitrootcause; Historical evidence; current hardware state UNKNOWN.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only NONE.
- **Sources:** [LITE3_INTEGRATION.md](../../../../Documents/NOMAD/docs/LITE3_INTEGRATION.md); [LITE3_HISTORY_AUDIT.md](../../../../Documents/NOMAD/docs/LITE3_HISTORY_AUDIT.md).
- **Remaining gap:** MISSING BOTH; Exact per-run raw artifact/configuration completeness qualified by provenance.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [TEST-20261002-013](tests/TEST-20261002-013-owner-reported-direct-nomad-strafe-failure.md), [FINDING-20261002-005](findings/FINDING-20261002-005-independent-body-frame-strafe-physical-proof-remains-incomplete.md).

#### HIST-066 — Supported stand RMS-only velocity loss persistence correction

- **Date / result / evidence:** UNKNOWN / FAIL→FIX→REPORTED_PASS / PRIMARY_PDF_HISTORICAL_REPORT.
- **Objective/configuration:** SAFETY; Measured-speed threshold0.15rad/s; RMS50ms;100ms RMS-only persistence.
- **Execution/observation:** PDF reports stable physical posture aborted by brief speed burst; persistence changed then stable computer stand/release reported
- **Cause → fix → retest:** Brief RMS-only transient interpreted as sustained hold loss; distinct from later raw-speed .51464rad/s body-shift abort → 100ms persistence for RMS-only hold loss; tilt/position/stale/invalid retained → Stable stand/release reported; raw synchronized bundle missing.
- **Lesson/status:** Preserve chronology: CURRENT_STATUS older50ms text differs from source100ms; never apply this to raw body-shift speed guard; Historical evidence; no current hardware acceptance implied.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only [TEST-20260913-001](tests/TEST-20260913-001-long-supported-stand-release.md).
- **Sources:** [Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf](../../../../Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf); [supervised_stand_monitor.hpp](../../state_machine/supervised_stand_monitor.hpp).
- **Remaining gap:** MISSING BOTH; Exact run date, SHA, and primary capture bundle missing.
- **Final coverage:** MISSING BOTH; expected TEST_SESSION, FINDING; NONE.

#### HIST-067 — Early normalized ROS manual-axis fail-closed sitting test

- **Date / result / evidence:** UNKNOWN / PASS_NEGATIVE_PATH / PRIMARY_PDF_HISTORICAL_REPORT.
- **Objective/configuration:** ROBOT_CONTROL; sensor_visualization/lite3_manual_axis_control; forward±.10;300ms;state6;battery25%;transmitfalse default.
- **Execution/observation:** Dry-run no network; live deadman/state gate blocked movement
- **Cause → fix → retest:** Standing/deadman readiness absent → Fail-closed neutral behavior → Later separately reported direction tests.
- **Lesson/status:** A negative-path live pass does not prove locomotion; Historical evidence; no current hardware acceptance implied.
- **Coverage:** MISSING BOTH; evidence PARTIALLY. Direct NONE. Related only [FINDING-20260914-001](findings/FINDING-20260914-001-vendor-manual-axis-protocol.md).
- **Sources:** `PDF A pp5–6`.
- **Remaining gap:** MISSING BOTH; Exact run date, SHA, and primary capture bundle missing.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION; NONE.

#### HIST-068 — Historical backward and bidirectional yaw validation

- **Date / result / evidence:** UNKNOWN / REPORTED_PASS / PRIMARY_PDF_HISTORICAL_REPORT.
- **Objective/configuration:** ROBOT_CONTROL; Forward+.10→9174;backward-.10→-9175;ROSyaw+.25→-13107,-.25→13106.
- **Execution/observation:** Physical backward and both yaw signs reported; neutral/deadman/shutdown reported; no pure lateral proof
- **Cause → fix → retest:** UNKNOWN → Source-qualified vendor commands and inverted asymmetric yaw encoding → Exact individual dates/logs missing.
- **Lesson/status:** Normalized values are not calibrated SI speeds; early yaw cap.25 differs product Nav2.20; Historical evidence; no current hardware acceptance implied.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only [FINDING-20260914-001](findings/FINDING-20260914-001-vendor-manual-axis-protocol.md), [TEST-20260927-004](tests/TEST-20260927-004-laptop-xbox-manual.md).
- **Sources:** `PDF A pp6–7,12`; [Lite3_Full_Project_Complete_HE_2026-09-27.pdf](../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf).
- **Remaining gap:** MISSING BOTH; Exact run date, SHA, and primary capture bundle missing.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20261002-021](tests/TEST-20261002-021-historical-ros-vendor-backward-motion.md), [TEST-20261002-022](tests/TEST-20261002-022-historical-ros-vendor-yaw-in-both-directions.md), [TEST-20261002-024](tests/TEST-20261002-024-historical-ros-deadman-release-neutral-and-shutdown.md), [FINDING-20261002-015](findings/FINDING-20261002-015-historical-normalized-vendor-axes-are-not-si-calibration.md).

#### HIST-069 — Historical stronger curved cmd_vel motion

- **Date / result / evidence:** UNKNOWN / REPORTED_PASS / PRIMARY_PDF_HISTORICAL_REPORT.
- **Objective/configuration:** ROBOT_CONTROL; linear.x+.10 angular.z+.15 linear.y0 duration≈.77s.
- **Execution/observation:** Forward plus turning physically confirmed in primary summary
- **Cause → fix → retest:** UNKNOWN → NONE → UNKNOWN.
- **Lesson/status:** Curved motion and world lateral displacement do not prove direct body strafe; Historical evidence; no current hardware acceptance implied.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only [FINDING-20260914-001](findings/FINDING-20260914-001-vendor-manual-axis-protocol.md).
- **Sources:** `PDF A pp7–8`.
- **Remaining gap:** MISSING BOTH; Exact run date, SHA, and primary capture bundle missing.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20261002-023](tests/TEST-20261002-023-historical-ros-forward-and-yaw-curved-motion.md), [FINDING-20261002-015](findings/FINDING-20261002-015-historical-normalized-vendor-axes-are-not-si-calibration.md).

#### HIST-070 — Earlier LiDAR orientation, clustering and mapping work

- **Date / result / evidence:** UNKNOWN / PARTIAL / PRIMARY_PDF_HISTORICAL_REPORT.
- **Objective/configuration:** SENSORS; RPLIDAR S2/sllidar_ros2;~10Hz;lidar z≈.08m yawπ.
- **Execution/observation:** Historical sensor and map operation reported; at A writing LiDAR USB disconnected and calibration blocked
- **Cause → fix → retest:** Orientation confusion; exact metrology unknown → Historical yawπ frame correction → Later LiDAR product path independently reported.
- **Lesson/status:** Do not transplant frame transform into floor-projected NOMAD base without measurement; Historical evidence; no current hardware acceptance implied.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only [TEST-20260927-003](tests/TEST-20260927-003-home-map-localization.md).
- **Sources:** `PDF A pp2,8–9`; `PDF B pp4,6–7`.
- **Remaining gap:** MISSING BOTH; Exact run date, SHA, and primary capture bundle missing.
- **Final coverage:** PARTIALLY; expected TEST_SESSION, FINDING; [FINDING-20261002-013](findings/FINDING-20261002-013-configured-lidar-extrinsics-are-not-complete-calibration-metrology.md).

#### HIST-071 — Earlier D455 RGB/depth and center-depth range checks

- **Date / result / evidence:** UNKNOWN / PARTIAL / PRIMARY_PDF_HISTORICAL_REPORT.
- **Objective/configuration:** SENSORS; ROS2 D455 streams;RViz;exact extrinsic UNKNOWN.
- **Execution/observation:** Historical RGB/depth operated; later on-demand to reduce CPU; no calibrated perception/Nav2 consumer acceptance
- **Cause → fix → retest:** UNKNOWN → On-demand workload policy later → Exact depth accuracy/extrinsics unproven.
- **Lesson/status:** Earlier hardware use can be recorded while current product perception remains unvalidated; Historical evidence; no current hardware acceptance implied.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only NONE.
- **Sources:** `PDF A pp2,8`; `PDF B pp4,9`.
- **Remaining gap:** MISSING BOTH; Exact run date, SHA, and primary capture bundle missing.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION; NONE.

#### HIST-072 — Calibration logger and monitor preparation

- **Date / result / evidence:** UNKNOWN / PASS_OFFLINE_ONLY / PRIMARY_PDF_HISTORICAL_REPORT.
- **Objective/configuration:** ODOMETRY; cmd_vel/normalized axes/deadman/odom/ICP quality synchronized; transmissionfalse.
- **Execution/observation:** Build/offline tests passed; zero robot commands; LiDAR disconnected at summary time
- **Cause → fix → retest:** Physical velocity/odom calibration incomplete → Logging infrastructure → Physical calibration not executed in preparation.
- **Lesson/status:** Prepared recorder is not measured calibration; Historical evidence; no current hardware acceptance implied.
- **Coverage:** MISSING BOTH; evidence PARTIALLY. Direct NONE. Related only [TEST-20260915-002](tests/TEST-20260915-002-icp-threshold-candidates.md).
- **Sources:** `PDF A p9`.
- **Remaining gap:** MISSING BOTH; Exact run date, SHA, and primary capture bundle missing.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION; NONE.

#### HIST-073 — Independent scan-match versus AMCL pose disagreement

- **Date / result / evidence:** UNKNOWN / INCONCLUSIVE / PRIMARY_PDF_HISTORICAL_REPORT.
- **Objective/configuration:** LOCALIZATION; Correct map/LiDAR diagnostic; AMCL pose.
- **Execution/observation:** Map/scan could align >80% while AMCL pose offset≈22.5cm; raw search/index absent
- **Cause → fix → retest:** AMCL pose mismatch supported; cause UNKNOWN → No verified permanent fix from PDF → Reference97–99%reported separately.
- **Lesson/status:** Independent alignment score is diagnostic, not permission to tune map/extrinsic; Historical evidence; no current hardware acceptance implied.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only [TEST-20260927-003](tests/TEST-20260927-003-home-map-localization.md).
- **Sources:** `PDF B p7`.
- **Remaining gap:** MISSING BOTH; Exact run date, SHA, and primary capture bundle missing.
- **Final coverage:** FULLY; expected FINDING; [FINDING-20261002-004](findings/FINDING-20261002-004-localization-confidence-is-a-custom-scan-to-map-match-score.md).

#### HIST-074 — Earlier chair planning safe refusal

- **Date / result / evidence:** UNKNOWN / PASS_SAFE_REFUSAL; RAW BUNDLE INCOMPLETE / PRIMARY_PDF_HISTORICAL_REPORT.
- **Objective/configuration:** NAVIGATION; 17valid paths;LEFT goal~1.30m forward/.60m left,path~1.49m;body.610×.370m.
- **Execution/observation:** Independent clearance0.00m at initial pose; motion NONE; Day2 still OPEN at this PDF snapshot
- **Cause → fix → retest:** Reported unsafe initial clearance; later tangent-yaw diagnostic defect may be separate; no proven causal linkage → Refuse motion; later accepted chair sessions independent → Later partial/pass in contemporary closeout; exact relation/dateUNKNOWN.
- **Lesson/status:** Do not replace safe refusal with later movement PASS or assume diagnostic bug caused it; Historical evidence; no current hardware acceptance implied.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only [TEST-20260927-001](tests/TEST-20260927-001-chair-avoidance-interrupted.md), [TEST-20260927-002](tests/TEST-20260927-002-chair-avoidance-pass.md), [FINDING-20260927-003](findings/FINDING-20260927-003-obstacle-snapshot.md).
- **Sources:** `PDF B p8`; [Lite3_Day1_Day2_Summary_HE.pdf](../../../../Desktop/robot_dog/Lite3_Day1_Day2_Summary_HE.pdf).
- **Remaining gap:** MISSING BOTH; Exact run date, SHA, and primary capture bundle missing.
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20261002-005](tests/TEST-20261002-005-earlier-chair-planning-safe-refusal.md).

#### HIST-075 — High-level robot stand lease loss and recovery

- **Date / result / evidence:** UNKNOWN / FAIL→FIX→REPORTED_PASS / PRIMARY_PDF_HISTORICAL_REPORT.
- **Objective/configuration:** ROBOT_CONTROL; Temporary source lease; neutral heartbeat during preflight; competing C2.
- **Execution/observation:** Lease lost during tests; after fix terminal Stand→STANDING→velocity0→lease released→NONE physically reported
- **Cause → fix → retest:** Neutral heartbeat absence/competing C2 per summary; raw exact chain missing → Preserve neutral heartbeat and remove competing C2 → Dedicated robot stand success reported; down physical acceptance missing.
- **Lesson/status:** Separate high-level lease recovery from low-level atomic entry and RMS hold fixes; Historical evidence; no current hardware acceptance implied.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only [TEST-20260927-004](tests/TEST-20260927-004-laptop-xbox-manual.md).
- **Sources:** `PDF B pp8–9`; `PDF D p2`.
- **Remaining gap:** MISSING BOTH; Exact run date, SHA, and primary capture bundle missing.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [TEST-20261002-004](tests/TEST-20261002-004-high-level-robot-stand-temporary-lease-acceptance.md), [FINDING-20261002-008](findings/FINDING-20261002-008-temporary-high-level-posture-leases-need-neutral-continuity.md).

#### HIST-076 — Relocalize started before explicit approval

- **Date / result / evidence:** UNKNOWN / FAIL→FIX→OFFLINE_PASS / PRIMARY_PDF_HISTORICAL_REPORT_AND_COMMITTED_TESTS.
- **Objective/configuration:** SAFETY; Bounded recovery CLI; AUTONOMY lease.
- **Execution/observation:** Summary says relocalize started without approval; fixed so no ownership/motion before explicit y
- **Cause → fix → retest:** Approval gating absent/too late in historical CLI → Explicit default-no approval before ownership → TEST-20260929-001 offline cancel/approval; complete physical CLI still incomplete.
- **Lesson/status:** Historical failure is distinct from the later correct offline record; Historical evidence; no current hardware acceptance implied.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only [TEST-20260929-001](tests/TEST-20260929-001-relocalize-approval.md).
- **Sources:** `PDF B p9`; `PDF D p2`; [TEST-20260929-001-relocalize-approval.md](tests/TEST-20260929-001-relocalize-approval.md).
- **Remaining gap:** MISSING BOTH; Exact run date, SHA, and primary capture bundle missing.
- **Final coverage:** MISSING TEST SESSION; expected TEST_SESSION, FINDING; [FINDING-20261002-009](findings/FINDING-20261002-009-relocalization-requires-explicit-approval-before-ownership-or-motion.md).

#### HIST-077 — Charging spark and suspected Mini-PC DC-DC damage

- **Date / result / evidence:** UNKNOWN / INCIDENT; ROOT INCONCLUSIVE / PRIMARY_PDF_HISTORICAL_REPORT.
- **Objective/configuration:** HARDWARE; Battery connected while charging; exact unit/config/dateUNKNOWN.
- **Execution/observation:** Spark and suspected Mini-PC DC-DC damage; component failure unconfirmed
- **Cause → fix → retest:** Exact electrical cause UNKNOWN → Separate power integration hardening; no proven repair → UNKNOWN.
- **Lesson/status:** Keep electrical incidents separate from software/network root causes; Historical evidence; no current hardware acceptance implied.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only NONE.
- **Sources:** `PDF B p10`.
- **Remaining gap:** MISSING BOTH; Exact run date, SHA, and primary capture bundle missing.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [TEST-20261002-015](tests/TEST-20261002-015-battery-connection-spark-and-suspected-dc-dc-damage.md), [FINDING-20261002-010](findings/FINDING-20261002-010-battery-connection-spark-and-suspected-dc-dc-damage-need-separate-closure.md).

#### HIST-078 — Lithium battery charging fire

- **Date / result / evidence:** UNKNOWN / INCIDENT / PRIMARY_PDF_HISTORICAL_REPORT.
- **Objective/configuration:** HARDWARE; Charging battery; exact unit/date/configUNKNOWN.
- **Execution/observation:** Fire service called; robot remained operational; rear shell damaged
- **Cause → fix → retest:** Battery fire during charging; mechanism UNKNOWN → Power/battery hardening remains open → Operational robot report is not safety closure.
- **Lesson/status:** Preserve hardware incident without invented mechanism or chronology; Historical evidence; no current hardware acceptance implied.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only NONE.
- **Sources:** `PDF B p10`.
- **Remaining gap:** MISSING BOTH; Exact run date, SHA, and primary capture bundle missing.
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [TEST-20261002-020](tests/TEST-20261002-020-lithium-battery-charging-fire-and-reported-shell-damage.md), [FINDING-20261002-014](findings/FINDING-20261002-014-reported-lithium-charging-fire-has-no-recorded-safety-closure.md).

#### HIST-079 — Persistent runtime separated from Xbox

- **Date / result / evidence:** UNKNOWN / UNKNOWN → PASS / HISTORICAL_CLAIM / LIVE_STATIC_PROVEN.
- **Objective/configuration:** ROBOT_CONTROL, SAFETY; See listed primary sources; exact deployed run configuration UNKNOWN.
- **Execution/observation:** Optional source lifecycle was entangled with critical heartbeat/telemetry.; Persistent sole UDP43897 runtime; manual disconnect clears authorization/velocity, heartbeat/odom/TF survive.
- **Cause → fix → retest:** Only the explicitly reported mechanism in the stages is supported; exact per-run cause UNKNOWN when not captured → Persistent sole UDP43897 runtime; manual disconnect clears authorization/velocity, heartbeat/odom/TF survive. → Persistent sole UDP43897 runtime; manual disconnect clears authorization/velocity, heartbeat/odom/TF survive..
- **Lesson/status:** Add scoped retrospective live-static session; retain single-owner finding.; Evidence-bounded historical scope; exact physical acceptance only when explicitly recorded.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only [FINDING-20260930-001](findings/FINDING-20260930-001-command-authority.md).
- **Sources:** [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md); [ENGINEERING_KNOWLEDGE_BASE.md](../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- **Remaining gap:** No dedicated disconnect/heartbeat raw trace or deployment manifest..
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20261002-025](tests/TEST-20261002-025-persistent-runtime-survives-optional-xbox-source-loss.md).

#### HIST-080 — AMCL global service hung while sensors fresh

- **Date / result / evidence:** UNKNOWN / FAIL → PARTIAL / LIVE_STATIC_PROVEN / PARTIAL.
- **Objective/configuration:** LOCALIZATION, ROS2; See listed primary sources; exact deployed run configuration UNKNOWN.
- **Execution/observation:** 55.1% unchanged; scan~10Hz/odom~50Hz; global service/lifecycle/amcl_pose unresponsive.; Restart localization only, reset particle state, require fresh convergence/manual disambiguation.
- **Cause → fix → retest:** Only the explicitly reported mechanism in the stages is supported; exact per-run cause UNKNOWN when not captured → Restart localization only, reset particle state, require fresh convergence/manual disambiguation. → .
- **Lesson/status:** New session/finding; do not infer sensor failure or restart runtime casually.; Evidence-bounded historical scope; exact physical acceptance only when explicitly recorded.
- **Coverage:** MISSING BOTH; evidence PARTIALLY. Direct NONE. Related only NONE.
- **Sources:** [TROUBLESHOOTING.md](../../onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md).
- **Remaining gap:** No dedicated terminal/journal capture..
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [TEST-20261002-028](tests/TEST-20261002-028-amcl-global-localization-service-hung-with-fresh-sensors.md), [FINDING-20261002-016](findings/FINDING-20261002-016-fresh-scan-and-odometry-do-not-prove-responsive-amcl.md).

#### HIST-081 — Startup-relative HIGH-LEVEL odom displacement validation

- **Date / result / evidence:** UNKNOWN / PASS / HISTORICAL_CLAIM.
- **Objective/configuration:** ODOMETRY; See listed primary sources; exact deployed run configuration UNKNOWN.
- **Execution/observation:** Catalog reports physical1m-style validation and product motion exercised odom.
- **Cause → fix → retest:** Only the explicitly reported mechanism in the stages is supported; exact per-run cause UNKNOWN when not captured →  → .
- **Lesson/status:** Create HISTORICAL_CLAIM retrospective session only; do not invent measured tolerance.; Evidence-bounded historical scope; exact physical acceptance only when explicitly recorded.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only NONE.
- **Sources:** [TEST_CATALOG.md](../testing/TEST_CATALOG.md); [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md); [CONFIGURATION_CALIBRATION_DATA.md](../architecture/CONFIGURATION_CALIBRATION_DATA.md).
- **Remaining gap:** No actual start/end/tolerance/body-frame measurement, robot-specific calibration or raw run..
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20261002-016](tests/TEST-20261002-016-historical-product-odometry-displacement-claim.md).

#### HIST-082 — Planner unavailable while localizationactive

- **Date / result / evidence:** UNKNOWN / FAIL → PASS / HISTORICAL_CLAIM / OFFLINE_PROVEN.
- **Objective/configuration:** NAVIGATION; See listed primary sources; exact deployed run configuration UNKNOWN.
- **Execution/observation:** Nav2navigationservice notrunning; MapServer/AMCLactive alone insufficient.; Motion command may start existingNav2 only solemissingcondition thencheckservers/costmaps; read-onlystatusneverstarts.
- **Cause → fix → retest:** Only the explicitly reported mechanism in the stages is supported; exact per-run cause UNKNOWN when not captured → Motion command may start existingNav2 only solemissingcondition thencheckservers/costmaps; read-onlystatusneverstarts. → Motion command may start existingNav2 only solemissingcondition thencheckservers/costmaps; read-onlystatusneverstarts..
- **Lesson/status:** Finding and session; preserve separation localization/navigation readiness.; Evidence-bounded historical scope; exact physical acceptance only when explicitly recorded.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only NONE.
- **Sources:** [FAILURES_AND_FIXES.md](../FAILURES_AND_FIXES.md); [OBSTACLE_TEST.md](../operations/OBSTACLE_TEST.md).
- **Remaining gap:** Liveinstalledretest absent..
- **Final coverage:** FULLY; expected TEST_SESSION, FINDING; [TEST-20261002-030](tests/TEST-20261002-030-obstacle-preflight-separated-localization-from-inactive-nav2.md), [FINDING-20261002-017](findings/FINDING-20261002-017-active-localization-does-not-mean-nav2-servers-are-available.md).

#### HIST-083 — Duplicate RViz/config launcher disagreement

- **Date / result / evidence:** UNKNOWN / FAIL → PASS / HISTORICAL_CLAIM / LIVE_STATIC_PROVEN.
- **Objective/configuration:** DEPLOYMENT; See listed primary sources; exact deployed run configuration UNKNOWN.
- **Execution/observation:** Multiplelaunchers/watchers/configsourcesduplicatewindows/restoreoverlays.; Canonical laptopconfig/singleinstancewatcher;liveoperatorviewvalidated.
- **Cause → fix → retest:** Only the explicitly reported mechanism in the stages is supported; exact per-run cause UNKNOWN when not captured → Canonical laptopconfig/singleinstancewatcher;liveoperatorviewvalidated. → Canonical laptopconfig/singleinstancewatcher;liveoperatorviewvalidated..
- **Lesson/status:** Retrospectivesession+finding or consolidate headless lesson.; Evidence-bounded historical scope; exact physical acceptance only when explicitly recorded.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only NONE.
- **Sources:** [ENGINEERING_KNOWLEDGE_BASE.md](../operations/ENGINEERING_KNOWLEDGE_BASE.md); [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- **Remaining gap:** Exact processcapture absent; hostGUIvalidation not robotmotionproof..
- **Final coverage:** MISSING BOTH; expected TEST_SESSION, FINDING; NONE.

#### HIST-084 — Distro paho compatibility defect→shim

- **Date / result / evidence:** UNKNOWN / UNKNOWN → PASS → PASS / HISTORICAL_CLAIM / OFFLINE_PROVEN / LIVE_STATIC_PROVEN.
- **Objective/configuration:** MQTT; See listed primary sources; exact deployed run configuration UNKNOWN.
- **Execution/observation:** GatewayclientAPIneeded distrocompatibility; precise liveexception notretained.; NestedNOMADcommit e1990e1 mqtt_compat and tests.; Latera0cda36aggregategatewayvalidation.
- **Cause → fix → retest:** Only the explicitly reported mechanism in the stages is supported; exact per-run cause UNKNOWN when not captured → NestedNOMADcommit e1990e1 mqtt_compat and tests. → NestedNOMADcommit e1990e1 mqtt_compat and tests.; Latera0cda36aggregategatewayvalidation..
- **Lesson/status:** Findingwithcommitevidence; associateaggregateintegrationtestwithoutclaimingisolatedliveretest.; Evidence-bounded historical scope; exact physical acceptance only when explicitly recorded.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only NONE.
- **Sources:** [mqtt_compat.py](../../../NOMAD/ros2_ws/src/nomad_bipolix_gateway/nomad_bipolix_gateway/mqtt_compat.py); [BIPOLIX_NON_MOTION_MVP.md](../../../NOMAD/docs/integrations/BIPOLIX_NON_MOTION_MVP.md).
- **Remaining gap:** Inspect gitdiff for exactpath/API; no invented failingtrace..
- **Final coverage:** MISSING FINDING; expected FINDING; NONE.

#### HIST-085 — NamespacedC&C versuslocaledgecontroltopics

- **Date / result / evidence:** UNKNOWN / PASS → PASS / OFFLINE_PROVEN / LIVE_STATIC_PROVEN.
- **Objective/configuration:** MQTT; See listed primary sources; exact deployed run configuration UNKNOWN.
- **Execution/observation:** 9739f4cuseslocalcontrol/platform_*;robotidvalidated;testupdated.; LaterPhase3Blivetrafficrecord.
- **Cause → fix → retest:** Only the explicitly reported mechanism in the stages is supported; exact per-run cause UNKNOWN when not captured → 9739f4cuseslocalcontrol/platform_*;robotidvalidated;testupdated. → 9739f4cuseslocalcontrol/platform_*;robotidvalidated;testupdated.; LaterPhase3Blivetrafficrecord..
- **Lesson/status:** Dedicated topologyfinding linking9739f4c andcanonicalPhase3Bsession.; Evidence-bounded historical scope; exact physical acceptance only when explicitly recorded.
- **Coverage:** MISSING BOTH; evidence PARTIALLY. Direct NONE. Related only [TEST-20261001-001](tests/TEST-20261001-001-nomad-phase3b-live-static.md).
- **Sources:** [BIPOLIX_PHASE3B_LIVE_BLOCKED.md](../../../NOMAD/docs/integrations/BIPOLIX_PHASE3B_LIVE_BLOCKED.md); [BIPOLIX_NON_MOTION_MVP.md](../../../NOMAD/docs/integrations/BIPOLIX_NON_MOTION_MVP.md).
- **Remaining gap:** No originaldroppedtopiccapture; rawtransporttrace absent..
- **Final coverage:** FULLY; expected FINDING; [FINDING-20261002-012](findings/FINDING-20261002-012-mqtt-edge-namespace-translation-is-part-of-the-transport-contract.md).

#### HIST-086 — Updated gatewayunits were not restarted by deploy

- **Date / result / evidence:** UNKNOWN / PASS → PASS / OFFLINE_PROVEN / LIVE_STATIC_PROVEN.
- **Objective/configuration:** DEPLOYMENT; See listed primary sources; exact deployed run configuration UNKNOWN.
- **Execution/observation:** 6df9c00restartupdatedgatewayunits+deployregression.; a0cda36livevalidationafterfix.
- **Cause → fix → retest:** Only the explicitly reported mechanism in the stages is supported; exact per-run cause UNKNOWN when not captured → 6df9c00restartupdatedgatewayunits+deployregression. → 6df9c00restartupdatedgatewayunits+deployregression.; a0cda36livevalidationafterfix..
- **Lesson/status:** Deploymentfinding forupdatedsource≠runningprocess; crosslinksourceoftruth.; Evidence-bounded historical scope; exact physical acceptance only when explicitly recorded.
- **Coverage:** MISSING BOTH; evidence PARTIALLY. Direct NONE. Related only [TEST-20261001-001](tests/TEST-20261001-001-nomad-phase3b-live-static.md), [FINDING-20260929-001](findings/FINDING-20260929-001-source-of-truth.md).
- **Sources:** [deploy_bipolix_phase3b.sh](../../../NOMAD/scripts/edge/deploy_bipolix_phase3b.sh); [BIPOLIX_NON_MOTION_MVP.md](../../../NOMAD/docs/integrations/BIPOLIX_NON_MOTION_MVP.md).
- **Remaining gap:** No before/afterunit/executablemanifest; do not infer everydeployedhostmatched..
- **Final coverage:** FULLY; expected FINDING; [FINDING-20261002-011](findings/FINDING-20261002-011-updated-gateway-source-must-become-the-running-deployed-process.md).

#### HIST-087 — Phase3C adapter/Stand workflow andconnectivityfix

- **Date / result / evidence:** UNKNOWN / PASS → PLANNED / OFFLINE_PROVEN / PLANNED.
- **Objective/configuration:** NOMAD, ROBOT_CONTROL; See listed primary sources; exact deployed run configuration UNKNOWN.
- **Execution/observation:** 35c8173adapter;494df95protectedStandworkflow;cc9cd69decoupleconnectedfromodomprobe;tests.; Firstprotectedbrowserforward/STOP notexecuted;actualUNKNOWN.
- **Cause → fix → retest:** Only the explicitly reported mechanism in the stages is supported; exact per-run cause UNKNOWN when not captured →  → .
- **Lesson/status:** NewOFFLINE_PROVENsessionforcommittedworkflow; updateprovenance only;plannedrecord staysPLANNED.; Evidence-bounded historical scope; exact physical acceptance only when explicitly recorded.
- **Coverage:** MISSING BOTH; evidence PARTIALLY. Direct NONE. Related only [TEST-20261001-002](tests/TEST-20261001-002-phase3c-xbox-physical.md), [FINDING-20261001-004](findings/FINDING-20261001-004-vendor-state-98.md), [FINDING-20261001-003](findings/FINDING-20261001-003-firefox-gamepad.md).
- **Sources:** [2026-10-01-bipolix-phase3c-physical-teleop-design.md](../../../NOMAD/docs/superpowers/specs/2026-10-01-bipolix-phase3c-physical-teleop-design.md); [CURRENT_STATE.md](CURRENT_STATE.md).
- **Remaining gap:** Canonicalwordinguncommittedisstaleatcleancc9cd69; noautomaticdeploy/physicalproof..
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20261002-014](tests/TEST-20261002-014-committed-phase-3c-stand-and-connectivity-software.md).

#### HIST-088 — Phases4–5 Mission/Patrol mockpreview

- **Date / result / evidence:** UNKNOWN / PASS → PASS → UNKNOWN / OFFLINE_PROVEN / LIVE_STATIC_PROVEN / INCONCLUSIVE.
- **Objective/configuration:** NOMAD; See listed primary sources; exact deployed run configuration UNKNOWN.
- **Execution/observation:** c3c3e96motionblockedMOCKmissionpatrolcontracts/preview.; Phase3Brobot-offlinerejectedrequests.; RealNav2mission/patrolarrival/cancel/pause/takeover pending.
- **Cause → fix → retest:** Only the explicitly reported mechanism in the stages is supported; exact per-run cause UNKNOWN when not captured →  → .
- **Lesson/status:** DedicatedOFFLINEsession; keepphysicalpending.; Evidence-bounded historical scope; exact physical acceptance only when explicitly recorded.
- **Coverage:** MISSING BOTH; evidence PARTIALLY. Direct NONE. Related only NONE.
- **Sources:** [BIPOLIX_NON_MOTION_MVP.md](../../../NOMAD/docs/integrations/BIPOLIX_NON_MOTION_MVP.md).
- **Remaining gap:** CapabilitymatrixlinksMVP but no dedicatedcanonicaltestforoffline4/5; standalonechairPASSdoesnottransfer..
- **Final coverage:** FULLY; expected TEST_SESSION; [TEST-20261002-019](tests/TEST-20261002-019-motion-blocked-nomad-mission-and-patrol-software.md).

#### HIST-089 — Operator Python helper lacked sourced ROS environment

- **Date / result / evidence:** UNKNOWN / FAIL → PASS / HISTORICAL_CLAIM.
- **Objective/configuration:** DEPLOYMENT, ROS2; See listed primary sources; exact deployed run configuration UNKNOWN.
- **Execution/observation:** PDF B p9 reports missing rclpy when operator helper shell lacked ROS environment.; Operator wrapper sources ROS and workspace automatically; fresh-shell command lookup and read-only status verified in closeout.
- **Cause → fix → retest:** Only the explicitly reported mechanism in the stages is supported; exact per-run cause UNKNOWN when not captured → Operator wrapper sources ROS and workspace automatically; fresh-shell command lookup and read-only status verified in closeout. → .
- **Lesson/status:** Optional deployment finding/session; separate environment import error from missing installed obstacle helper.; Evidence-bounded historical scope; exact physical acceptance only when explicitly recorded.
- **Coverage:** MISSING BOTH; evidence EVIDENCE INCOMPLETE. Direct NONE. Related only NONE.
- **Sources:** [Lite3_Full_Project_Complete_HE_2026-09-27.pdf](../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf); [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- **Remaining gap:** Exact traceback/date/deployed wrapper manifest absent; source report and wrapper implementation support environment lesson only..
- **Final coverage:** MISSING FINDING; expected FINDING; NONE.

## Reconstruction and capability gaps

- **down-pending** — Dedicated robot down CLI acceptance pending. Existing planned Phase3C test is only adjacent; canonical known issue explicitly tracks down. No PASS. CAPABILITY_OR_RECONSTRUCTION_GAP; not independently counted at initial reconstruction.
- **exact-score-leads** — Owner exact80.9% and98.3–100%samples. Needs timestamp,mapID,scorefield,thresholdcontext,rawtrace. CAPABILITY_OR_RECONSTRUCTION_GAP; not independently counted at initial reconstruction.
- **ble-dropout-lead** — BluetoothPIN/KeyMissing and~1min dropout. USB/XboxhistoricalsuccessnotBLEreliabilityproof. CAPABILITY_OR_RECONSTRUCTION_GAP; not independently counted at initial reconstruction.
- **nav-controller-avx** — SABLE MPPI SIGILL on Fitlet CPU without AVX. Commit source/body and root deployment metadata retained; no raw original SIGILL log or approved physical RPP acceptance. This is separate SABLE architecture, do not copy code into Bipolix. RESOLVED_TO_ROOT_MINIPC_INVENTORY; not independently counted at initial reconstruction.
- **standing-odom-drift** — SABLE standing gait telemetry created idle odometry/map drift. Field numbers are reported commit evidence, not independently measured raw dataset. The mitigation cannot establish accurate physical motion or current lidar/map alignment. RESOLVED_TO_ROOT_MINIPC_INVENTORY; not independently counted at initial reconstruction.

## Remaining canonical record gaps

| Event | Final coverage | Proposed action |
|---|---|---|
| HIST-024 | MISSING FINDING | Create a scoped retrospective Finding using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-026 | MISSING BOTH | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution.; Create a scoped retrospective Finding using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical… [full details in JSON] |
| HIST-028 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-029 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-030 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-032 | MISSING BOTH | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution.; Create a scoped retrospective Finding using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical… [full details in JSON] |
| HIST-033 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-035 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-036 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-037 | MISSING BOTH | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution.; Create a scoped retrospective Finding using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical… [full details in JSON] |
| HIST-038 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-039 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-040 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-041 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-042 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-043 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-044 | MISSING FINDING | Create a scoped retrospective Finding using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-047 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-048 | MISSING BOTH | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution.; Create a scoped retrospective Finding using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical… [full details in JSON] |
| HIST-060 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-066 | MISSING BOTH | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution.; Create a scoped retrospective Finding using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical… [full details in JSON] |
| HIST-067 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-070 | PARTIALLY | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution.; Capture early DBSCAN/clustering/map history only if original session or operator evidence can be recovered; leave unsupported details UNKNOWN. |
| HIST-071 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-072 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-076 | MISSING TEST SESSION | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-083 | MISSING BOTH | Create a scoped retrospective Test Session using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution.; Create a scoped retrospective Finding using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical… [full details in JSON] |
| HIST-084 | MISSING FINDING | Create a scoped retrospective Finding using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |
| HIST-089 | MISSING FINDING | Create a scoped retrospective Finding using listed sources; preserve UNKNOWN dates/root causes and raw evidence limitations; no new physical execution. |

Evidence completeness remains separate: 48 independent scopes retain EVIDENCE INCOMPLETE. Accessible local Codex history yielded 131 keyword-matching artifacts indexed as metadata leads; full conversational bodies were not exhaustively adjudicated and do not add physical proof or event counts.

The JSON crossmap resolves every gap-audit item to event IDs or an explicit reconstruction/root-pending disposition. Canonical records retain their source-relative links; this concise ledger uses links relative to this document and does not embed original record bodies.


## Subsequent missing-record capture

[Additional capture manifest](evidence/ADDITIONAL_HISTORICAL_CAPTURE_20261002.json) links each formerly missing record type to the same existing historical event ID; no additional historical execution is counted. Conservative HISTORICAL_CLAIM classification preserves unknown dates/SHAs/raw traces. [Retained offline simulation review](evidence/RETAINED_SIMULATION_REVIEW_20261002.json) adds verified row counts/hashes without rerunning simulations. All92 independent historical scopes are represented;48 raw evidence scopes remain incomplete, with no new physical acceptance. Current offline continuation is separate from historical event count.

## Final record totals after supervised preparation

87 Test Sessions /54 Findings; five additional stage plans107–111 contain no historical execution. All92 independent scopes represented;48 incomplete primary-evidence scopes remain. Earlier counts above are dated audit checkpoints.
