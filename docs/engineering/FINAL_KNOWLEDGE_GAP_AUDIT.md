# FINAL HISTORICAL KNOWLEDGE GAP + SABLE INTEGRATION AUDIT

2026-10-02. This closes an evidence audit of the existing integration; it does not reopen control implementation, deploy either branch, or conduct physical tests. Today's structured knowledge baseline remains the entry point. Older primary evidence was used to repair coverage with explicit provenance rather than silently superseding it.

## Deliverables and scope

- [Historical master inventory](HISTORICAL_MASTER_INVENTORY.md), with [structured event fields and coverage](HISTORICAL_MASTER_INVENTORY.json): chronology, objectives, configurations, executions, observations, results, evidence classes, failure causes, fixes, retests, lessons, source references, currentness and record IDs.
- [Mini-PC deployed-state audit](MINIPC_DEPLOYED_STATE_AUDIT.md), with curated non-secret facts and deployment findings.
- [SABLE integration closure audit](SABLE_INTEGRATION_CLOSURE_AUDIT.md): full command paths, capability comparison, architectural contribution classes, safety boundaries and minimum physical validation matrix.
- [Test Sessions](TEST_REGISTRY.md), [Engineering Findings](FINDING_REGISTRY.md), [Current State](CURRENT_STATE.md), [Capabilities](CAPABILITY_MATRIX.md), [Issues](KNOWN_ISSUES.md), [Lessons](LESSONS_LEARNED.md), [Known Good](KNOWN_GOOD_CONFIGURATIONS.md), [Known Bad](KNOWN_BAD.md).

The nine-column [current control-capability matrix and complete command paths](../../../../Documents/NOMAD/docs/LITE3_INTEGRATION.md#current-capability-matrix) remain in the authoritative product report; the closure/deployed-state reports add explicit differences from what currently runs on the Mini-PC.

## Source-of-truth boundaries

| Question | Best inspected evidence | What it does not establish |
|---|---|---|
| What we designed | Source/config/Git history in laptop Lite-robot cc9cd69; nested historical integration53d0692; current product bipolix_robot0c48b4d | Physical success or deployed equivalence |
| What we tested | Contemporary reports, recovered sessions, three historical PDFs, retained metrics and bag references | Complete raw per-run manifests for every historical claim |
| What actually ran on Mini-PC | Active service metadata, tracked-clean deployed mainb4f6a48, installed module hashes, effective configuration and bounded static observations | Full process-memory identity, physical motion/accuracy, current topic rates or telemetry delivery |
| What SABLE now implements locally | Five integration commits retaining product architecture; named tests and reviewed command paths | Deployment or physical acceptance of new laptop Xbox path |

Repository folder names are historical evidence labels; NOMAD remains the architectural source of truth. The target is Xbox on laptop → browser/Gamepad → NOMAD API → protected network → Mini-PC → authoritative ROS/vendor control. No Mini-PC Xbox device or LOCAL_XBOX readiness requirement is introduced.

## IMPORTANT HISTORICAL EXPERIMENTS

**Supported Stand/RL research:** objective was safe low-level posture and bounded zero-input policy research. Mechanically supported joint control reached a roughly203s stand and explicit release, while earlier stand attempts failed. Policy output, velocity/guard behavior and ownership acknowledgement were not interchangeable with product posture. Convergence/persistence, atomic permit use, absolute hold deadlines and gate-closing release were introduced in separate fixes. Lesson: keep low-level research outside product HIGH-LEVEL control, preserve every failure and use bounded permissions; SDK Release is not proof of dedicated product Sit/Down.

**Vendor control discovery:** objective was product motion without joint-control takeover. Bare/legacy command hypotheses and direct ONNX assumptions failed or remained inconclusive. Successful historical normalized forward/backward and both yaw directions used full SimpleCMD framing, exact raw axis encoding and yaw inversion. Historical ROS adapter deliberately forced y0. Lesson: protocol command existence is not robot capability evidence; preserve the exact historical path/configuration and distinguish normalized input from SI-scaled current input.

**Stand lease failure → fix → success:** product HIGH-LEVEL Stand initially failed with temporary ownership/heartbeat and competing C2 conditions. Neutral heartbeat and removal of the competing source preceded reported SITTING→STANDING success and return to NONE. This is separate from supported SDK Stand. Lesson: posture is an authoritative state transition, not successful dispatch; maintain neutral throughout a bounded posture transaction. Dedicated Down acceptance remains open.

**Body shift and FR unload:** objective was supported single-leg research. Raw-speed guard abort, permit lifecycle abort, failed unload/lift attempts, simulation contact-model ambiguity and parameter sweeps are preserved individually. Some later offline models passed, but that does not erase physical failures or validate every30/60/90 progression. Lesson: model feasibility, load evidence and physical acceptance are different gates; no transfer to product strafe or gait modes.

**ICP and TF:** objective was usable odometry/localization. ICP rejected correspondence around0.646 against0.70 and null-guess/recovery behavior failed; threshold candidates/replay were investigated, not physical proof. LiDAR orientation/TF ownership corrections addressed a different problem. Lesson: changing a threshold cannot replace correct frame geometry or sensor observability. AMCL owns map→odom, the robot odometry path owns odom→base_link; avoid duplicate TF authorities.

**Odometry flooding and DDS/lifecycle:** approximately154Hz callbacks and stale/disappearing ROS participants caused misleading service-active/readiness observations. Bounded latest-state processing at50Hz, discovery changes and lifecycle/localization-only recovery improved reported software/live-static behavior; long soak remains open. September24 retained bags show approximately200Hz in a different capture. Lesson: service active, process alive, topic fresh and authoritative robot state are separate predicates; preserve capture-specific rates. Do not restart the control owner casually to repair localization.

**Localization and chair avoidance:** wrong-map or ambiguous localization could show high custom scan confidence; a reported22.5cm AMCL offset illustrates why this is not an official pose probability. Early chair planning produced17 paths but clearance0 and safely refused motion. Later run was interrupted by power; subsequent right-detour physical PASS is retained separately from that PARTIAL result. Lesson: validated map identity, fresh pose, clearance and bounded execution all matter; world-frame detours/curves do not prove direct body-y strafe. Relocalization motion before approval was a failure; later approval/cancel fix and offline retest remain separate.

**Ownership/Lease Ghost:** objective was one authoritative writer across local Xbox, laptop Xbox and autonomy. Stale COMMAND_SOURCE markers outlived real owners, while leases, process locks and markers disagreed. Safe ZERO/release/cancel restored some paths; all-source parity and real dropout timing were not universally proven. Lesson: marker files cannot replace a live owner/lease, and recovery must discard old intent and require fresh neutral plus engagement. Historical local-Xbox PASS cannot validate the current networked NOMAD path.

**Resource/network/UI:** exporter child leaks starved SSH/resources; process-group cleanup was added. Headless optimization and on-demand D455 reduced historical resource load. Wi-Fi driver failures, broker endpoint drift, package/DNS failures and Firefox Gamepad mapping/focus behavior were different incidents. Lesson: network/service availability must be traced per hop; kernel js0 presence is not browser input readiness. Present configured D455-on deployment is distinct from historical on-demand policy. Structural leak fix presence is not a reliability soak.

**NOMAD Phases1–5:** read-only status, authority reservations, mock intent, live-static negative guards and guarded Phase3C software are preserved with their actual evidence classes. Phase3B deliberately rejected DRIVE when telemetry was absent. Phase3C first laptop controlled motion remained planned. Mock Mission/Patrol and software capability claims do not become real Nav2 acceptance. Phase4/5 named plans or expectations without adequate executed evidence remain HISTORICAL CLAIM/EVIDENCE INCOMPLETE.

**Deployed CPU and idle-odometry failures:** primary Git141b497 reports MPPI SIGILL on the AVX-less Mini-PC, followed by CPU-aware RPP selection. Gitb4f6a48 reports stationary gait telemetry integrated into odometry/map drift, followed by command-intent stillness suppression. Both fixes are deployed and absent from current integration. Lesson: merging an integration branch alone may regress separately learned field fixes; reconcile branches/configuration before any future deployment. This audit performed no retest.

**Hardware incidents:** suspected DC-DC/spark damage and later charging/fire are separate reports with incomplete chronology and root-cause proof. Do not merge them into a guessed single failure mechanism or successful repair narrative. Operational safety history remains relevant, but does not justify invented electrical diagnoses.

## HISTORICAL ENGINEERING LESSONS FOR CURRENT NOMAD INTEGRATION

1. Preserve one product authority and vendor writer. Reimplement ownership lessons inside existing API/edge/mux/driver owners; do not install a parallel historical arbiter.
2. Freshness is a prerequisite at every layer. Valid state98 is not STANDING; state6 must be fresh and authoritative. Status constants, stale markers and active services cannot authorize movement.
3. Safe recovery discards intent: ZERO, neutral, new owner/session and fresh RB edge; continuous deadman is required. Reconnect or a delayed reply must never replay held motion.
4. Physical evidence is path-specific. Preserve axes, sign, normalization, raw encoding, rate, deadzone, timeout and posture gates; any changed element requires scoped retest.
5. Lateral remains UNVALIDATED. Vendor0x0131 exists, historical ROSy0 prevented lateral output, prior NOMAD strafe failed with unknown cause. Do not infer gait/sign/rate fixes or lateral proof from curves/chair avoidance.
6. Correct frames and map identity precede tuning. Custom confidence percentages do not override ambiguous pose, wrong TF, zero clearance or missing authoritative localization.
7. Deployment provenance is part of readiness. Verify branch, installed resolution and effective overrides; preserve CPU/odom fixes and review site limits/sign before deployment.
8. Fail → investigate → fix → retest is the record. An offline pass, planned physical trial or later different-path PASS must not erase the failed experiment.

## Remaining evidence and technical gaps

Completeness means best available inspected engineering truth, not reconstruction of missing raw history. September1–7 and several exact experiment dates have no independently dated retained event. Early stand/RL tails, per-level body/load traces, calibration and bag payloads are incomplete. Full Mini-PC raw historical handoffs/runtime logs were not exported; central MQTT configuration was unreadable. Accessible local Codex history yielded131 keyword-matching artifacts, indexed for leads without treating conversational assertions as independent physical proof.

Virtual keyboard/body controls follow the shared product path, but virtual Xbox readiness currently lacks the expected Lite3 diagnostic contract; keep this functional limitation explicit. Leases are exclusive while active, not globally mandatory for preserved tokenless admin commands when no lease exists. No new safety bypass was found in the scoped source review; this is not hardware safety certification. Current integration physical validation and Mini-PC deployment reconciliation remain open.

## Verification and completion boundary

This audit changed knowledge/documentation only, not robot control implementation. Schema/ID/registry/local-link validation, inventory consistency, evidence provenance checks and whitespace checks are recorded in the final verification artifact. Physical test matrix is proposed in the closure audit and was not executed. No Mini-PC files/services/configuration changed, ownership acquired or robot commands sent.


## Final reproducible metrics and diff

92 independent engineering event/campaign scopes plus2 excluded aliases;63 FULLY represented,1 PARTIALLY,18 MISSING TEST SESSION,4 MISSING FINDING,6 MISSING BOTH. Coverage is canonical record representation, not raw completeness or physical acceptance.48 scopes retain incomplete raw evidence. All29 remaining record-gap scopes have explicit proposed actions in the inventory.

Baseline11 sessions/11 findings. Restored12 sessions/10 findings under original IDs. Added33 sessions/22 findings including the read-only Mini-PC audit: final56 sessions/43 findings. No claims of unique physical runs are inferred from record count.

Fresh checks, exact changed/new paths and `git diff --stat` are in [verification artifact](evidence/FINAL_AUDIT_VERIFICATION_20261002.json). Git statistics exclude untracked restored/new reports and records; their paths are separately listed. Major tracked changes update canonical summaries/provenance, clarify committed readiness source without physical promotion, and correct the obstacle override documentation to source-backed180seconds. NOMAD changes add closure pointers and deployed-state caveats to the two existing integration/history reports. No code or configuration was changed.

## Subsequent safe source closure — 2026-10-02

The read-only deployed snapshot remains unchanged. CPU-compatible controller selection and dispatch-bound idle odometry have subsequently been reconciled through existing SABLE owners, with offline tests only (TEST-20261002-106 / FINDING-20261002-095). Driver scaling diagnostics, bounded forwarding, UI evidence and passive validation preparation add observability without calibration changes. These are not deployed or physically proven. Direct strafe remains UNVALIDATED. See SAFE_AUTONOMOUS_CLOSURE.md for current counts, checks and blockers. Five additional supervised records TEST-20261002-107..111 are PLANNED ONLY, no new historical experiments; each physical matrix item is evaluated individually.
