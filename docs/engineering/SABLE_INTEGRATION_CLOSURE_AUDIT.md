# SABLE/NOMAD closure audit — 2026-10-02

Read-only review of branch `bipolix_robot`, HEAD `0c48b4d`, five commits c6461cc / fb4191d / a88f7be / dd817e9 / 0c48b4d against baseline5059f491. NOMAD Git status clean at initial inspection. Reviewed docs/LITE3_INTEGRATION.md and LITE3_HISTORY_AUDIT.md against actual current API, ControlAgent, ROS MQTT adapter/authority, mux, Lite3 driver, laptop input, and virtual cancellation code/tests. No robot, Mini-PC, ROS graph, UDP connection, deployment, or physical command used. Initial review wrote a /tmp report; this canonical document is the authorized documentation-only closeout. No integration code changed.

## Verdict

The present product command route remains one laptop/browser HTTP → fleet API → FleetRegistry MQTT → edge ControlAgent → MqttBridge/TeleopController → twist_mux → Lite3 bridge → vendor UDP route. Laptop Xbox is browser Gamepad input on the laptop, not Mini-PC /dev/input/js0 or LOCAL_XBOX. No added UI→ROS or UI→vendor UDP bypass was found. Existing optional local joy input is mux90, blocked by the persistent manual lock95; laptop teleop100 remains permitted. E-stop255 blocks all inputs.

The implementation incorporates the retained neutral/fresh-state/battery/ownership lessons in existing owners. Offline evidence supports these protections. It does not establish new physical acceptance. No confirmed new safety regression was found in the inspected paths, with the scope and evidence gaps below.

## Knowledge integration classification

| Class | Retained knowledge/current decision |
|---|---|
| ALREADY_EXISTED | Full vendor SimpleCMD encoding, asymmetric rounding, yaw inversion, bridge streaming/watchdog/heartbeat, single UDP owner, state-aware posture services, mux, ControlAgent TTL/retained suppression, persisted e-stop, patrol pause on teleop. |
| MIGRATED | Behavioral knowledge translated into NOMAD contracts: laptop Xbox axis mapping/deadzone and neutral/fresh RB protocol; body action integration through existing service maps. No directly copied historical component claimed. |
| LESSON_REIMPLEMENTED | Network source/lease ownership through API capability + public edge session, existing MQTT adapter and mux lock; reconnect disposal; virtual goal cancellation; bounded telemetry/readiness knowledge retained in documentation. Historical standalone arbiter/runtime not installed. |
| SAFETY_STRENGTHENED | Driver guard applies fresh standing/single source/known battery25%/transport hold to nav and axis formats, latches held motion; UI HTTP-stall release/fresh input; protected two-second lease; MQTT neutral-after-reset; persistent manual lock until fresh successful autonomy command; cancellation generation prevents old response releasing latest virtual transition. |
| NOT_MIGRATED_RD | ONNX/MotionSDK joint/leg control, experimental ICP, historic deployment/exporter/network/systemd stack, calibration/confidence overrides, second UDP/gateway/arbiter. |
| DUPLICATE | Competing authority/UDP stacks explicitly rejected; existing protocol/mux/driver retained. No newly introduced parallel vendor writer found. |
| UNVALIDATED | New end-to-end physical route, body-y lateral signs/gait/gain, SI scale, real controller/dropout timing, mode acknowledgement, firmware state98 activation assumptions, effective installed configuration. |
| RETEST | Every physical command/safety transition below; autonomy/clearance/localization separate from direct lateral acceptance. |

## Capability matrix

M = laptop controls/useTeleop → /fleet/.../teleop → ControlAgent robot/teleop → TeleopController teleop_vel → mux /cmd_vel → driver conversion/guard → UDP43893.
P = body API → ControlAgent robot/cmd → mapped ROS Trigger → state-aware shared SIT_STAND toggle. G = mapped mode Trigger, activation leave-posture/manual after settle. V = same API/MQTT/mux dispatch, simulated body/control output instead of vendor UDP.

| Capability | Current code path and support | Exact proven-path match / intentional difference | Result and retest |
|---|---|---|---|
| Stand | P; fresh single-source state, cooldown, no moving stream, e-stop gate; state6 confirms posture | Historical high-level Stand and low-level SDK reports are distinct. Current state-aware toggle and API/lease path are different | Offline support; new physical Stand/confirmation test required |
| Sit | P; same desired-state toggle, already-lying no-op | SDK Release is not dedicated Sit/Down proof | Dedicated physical Sit unvalidated; retest |
| Forward | M vx+; configured vx/3.4 sign+; full0x21010130 | Encoder matches historical normalized+.10→9174, full path/scaling does not. Current+.10SI→7324 | Historic other-path PASS, current offline only; retest/calibrate |
| Backward | M vx−; asymmetric negative rounding | Historical normalized−.10→−9175; current SI fraction differs | Historic other-path PASS; retest |
| Yaw left | M wz+; wz/4.5 sign−; full0x21010135 | Sign/encoder match old +.25normalized→−13107, current scale differs | Historic other-path PASS; retest |
| Yaw right | M wz−; inverted wire sign | Encoder matches old −.25normalized→13106, full route differs | Historic other-path PASS; retest |
| Forward/yaw curve | M simultaneous x,z | Old x+.10,z+.15/y0 curve report; independently scaled current values/authority differ | Historic reported PASS; current retest |
| Strafe left | M vy+; vy/1.6 sign+ full0x21010131 | Historical proven ROS adapter explicitly forced y=0. Protocol existence not physical motion proof | User NOMAD strafe FAIL preserved, exact direction/config/root cause UNKNOWN. Independent lateral investigation/retest required |
| Strafe right | M vy− | No per-sign direct lateral acceptance; Nav2 world-y detour is not proof | UNVALIDATED; investigate/retest |
| STOP | ExplicitStop sends API release even without engaged local source; QoS1 release→trailing zero; e-stop own latch/lock | Wire zero matches; HTTP/MQTT/mux latency differs | Offline supported; physical all-axis stop/latency test required |
| Deadman | Xbox fresh neutral, fresh RB edge, continuous RB; browser release events; .5s ROS/.4s driver watchdog | Old Xbox edge-only authorization differs from continuous guarded ROS/Phase3C/new browser path | Offline tests; physical RB release/dropout retest |
| Timeout | HTTP300ms stall release, edgeTTL1s, ROS.5s, driver.4s, state.5s | Historical guarded ROS .3s not same timings | Intentional existing default retention; measure total stop timing |
| Reconnect | Broker/uplink reset drops authority/target, retires session, requires release/fresh timestamped zero; UI suppresses held input | Same safety principle, different runtime/owner path | Offline tested; held-gesture network recovery retest |
| Controller disconnect | Gamepaddisconnect/absent-invalid selected pad clears input/revokes token; blur/hidden/unmount same | Historical local/BLE source proofs do not transfer | Offline coverage; browser USB/BLE event/poll dropout retest |
| Ownership takeover | Token+principal checks under API enqueue lock, edge public session + freshness, conflicting motion refused; pause and mux95 | Historical COMMAND_SOURCE arbiter not copied | Offline exclusivity tested; real competing client/source takeover retest |
| Autonomy | Existing sequencer/Nav2 nav_vel→same mux/driver; active lease blocks; manual hold persists on expiry/reset/restart; fresh successful start/resume/goto needed to unlock | Historic chair refusal→partial→later reported PASS retained; map/config/path differ | Physical takeover/cancel/stop/release retest independently |
| Virtual posture/mode | SimRobotControl stops old target; SimNav aborts old goals; KinematicBase cancellation-generation/confirmed neutral/new input gates | Instant simulated posture and starts standing/auto; no gait fidelity | Offline simulation support, no hardware proof |

## Safety trace and test evidence

- Stale or unknown standing state: driver `_drive_command` uses `axis_hold`, current state freshness and newer-than-axis-activation requirement; zero is returned and a live moving stream is latched. Held input remains zero when state recovers. Tests include `test_nav_telemetry_recovery_does_not_replay_a_held_command`, axis stale/stand-up latch tests.
- Unknown/low battery: `_battery_pct` returns None for missing/nonfinite level, `_drive_command` refuses None or <min_drive_battery25. Known24→80 recovery is tested for nav/axis and needs zero/new motion. Dedicated unknown/nonfinite battery recovery regression is less explicit in inspected tests: code coverage does not equal independent acceptance. Stand itself warns for low battery rather than denying; the strict battery25 guard is a drive contract, not a claim Stand is battery-gated.
- Transport failure: `_send` records transmit error; subsequent guard holds zero and latches current command; nav/axis injected-send-failure tests ensure held command does not restart even after2.3s transport recovery, then zero/new motion works. UDP send success is delivery evidence only; no vendor ACK. A send failure cannot guarantee physical receipt of neutral.
- MQTT reconnect held gesture: `link_reset` releases teleop, clears/retire authority, requires neutral, retains mux manual hold. `test_link_recovery_requires_release_or_zero_before_fresh_drive`; `test_zero_without_valid_fresh_timestamp_cannot_clear_reconnect_hold` covers missing/stale/future/bool/nonfinite cases. Explicit fail-safe release is allowed to clear neutral requirement; direction still needs valid owner/readiness/new browser input.
- Ownership invalid/recovery: API opaque token stays off MQTT; ControlAgent copies public session/expiry only; edge rejects stale/invalid claim, matching owner only; retired old session cannot reclaim during recovery window. `test_laptop_owner_requires_fresh_zero_and_excludes_foreign_drive`, `test_laptop_owner_blocks_autonomy_and_foreign_posture`, queued-expiry test and restart-lock test cover principal cases.
- Browser HTTP stall/inflight release: useTeleop releases and suppresses sources until fresh action; release-after-drain repeats release behind outstanding completed drives. Xbox renew/stand/request asynchronous results have generation checks; token loss/readiness false synchronously clears input. request/renew bounded900ms and poll stall300ms revoke.
- Virtual posture old motion: every SimRobotControl transition invokes stop. KinematicBase discards target and tracks cancellation generation; absent/unready/failing cancellation stays held; latest successful generation plus received zero needed, then fresh nonzero. `test_body_transition_cancels_nav2_and_requires_confirmation_and_zero` executes two transitions and requires >=2 requests; old response cannot release latest generation. `cancel_nav_goals=False` is an explicit configurable opt-out, used in dedicated inert tests; review effective config before stronger cancellation claims.
- Manual takeover unknown state: claim produces ownership/pause/manual lock, no stand or velocity; unknown/stale state6, activation or driver hold fails Xbox readiness. No button press/Request Control independently proves motion authorization. Manual hold persists after claim expiry/link reset, blocking actively publishing nav10/joy90. `test_manual_lock_requires_fresh_successful_autonomy_takeover` and restart test cover old/failed versus fresh/successful replies.

## Contract and evidence gaps

1. Lease is exclusive while active, not globally mandatory for all legacy clients: `ControlLeases.motion` accepts unleased tokenless admin commands when no API lease exists; `ControlAuthority.permits` similarly preserves unleased command mode without edge owner. Persistent mux95 blocks nav/joy, but teleop100 remains available. This is compatible preservation, not a second command architecture; document the boundary rather than claiming every motion requires Request Control.
2. Virtual laptop Xbox readiness is not proven: SimRobotControl diagnostics emit posture/mode/motion_hold, while xboxReadiness and Stand confirmation require Lite3 basic_state6/axis_activated/drive_hold fields. Keyboard/hold-button and virtual body paths are supported; inspected diagnostic producer alone cannot make Xbox ready on virtual robot. This appears a functional capability gap, not an unsafe bypass; no undocumented adapter was found in this trace.
3. Effective bringup driver config is axis/heartbeatON, standalone lite3 config defaults nav/heartbeatOFF. Physical equivalence depends on actual launch/profile/config. The later read-only Mini-PC audit inspected deployed launch/site allowlists, but did not sample the running ROS graph or controller messages. Current lateral sign+ explicitly UNVERIFIED.
4. No new raw physical logs/bags/per-run manifest/packet+posture captures, SI calibration, body-y displacement acceptance, USB/BLE dropout timing, actual neutral delivery/stop distance, or real competing-writer capture exists from this work.
5. Physical body actions deliberately refuse active moving stream; virtual actions immediately stop/discard intent. Simulation posture invalidation is not proof of physical Nav2 cancellation/ownership through every body transition.
6. Historical failure record remains failed/unknown cause; do not infer gait/sign/rate root cause. Historical forced-y0 policy and later Nav2 chair detour remain separate records. Old custom scan-match percentages/calibration not imported as official localization confidence.

## Verification provenance

Parent-provided prior runs: frontend1064, API368, ownership ROS143, other ROS243, colcon5; broad backend5382pass/30skip/4fail with corrected affected groups249. These figures were not independently rerun or converted into a clean full-backend pass here. Read actual named regression code rather than relying only on counts. This audit reran only inert pure ControlAuthority tests using PYTHONDONTWRITEBYTECODE=1 and pytest cache disabled: **3 passed in0.01s**. No ROS initialization, graphs or network/physical endpoint invocation occurred.

Closure status: engineering migration/guard review complete at inspected SHA; physical capability and hardware safety acceptance remain RETEST. Virtual Xbox readiness remains an explicit functional evidence gap. Do not promote historical PASS into current physical proof.


## Deployed versus integrated source — reconciliation required

Evidence: docs/engineering/MINIPC_DEPLOYED_STATE_AUDIT.md and evidence/MINIPC_READ_ONLY_20261002.json. The root auditor captured Mini-PC facts read-only; this reviewer accessed only those local artifacts and Git objects, never the Mini-PC. All41 snapshot records exactly matched their originating allowlisted /tmp capture records. SHA256 of the local Git b4f6a48 driver, MQTT adapter and navigation stack blobs exactly matched the three captured source/resolved-installed module hashes. No credentials, unit bodies, arbitrary journal/process text or bag payloads were copied into this closure document.

Mini-PC tracked-clean main b4f6a48 and laptop integration0c48b4d are separate branches. New ControlAuthority/manual lock/battery guards from this integration are absent from that captured deployment. Installed editable module resolution matches b4f6a48 source; already-imported process memory was not inspected. Therefore the current target laptop path is **implemented/offline tested, not deployed or physically accepted by this audit**.

Conversely, local integration0c48b4d lacks two useful deployed-source fixes:

- Git141b497 reports apt MPPI AVX SIGILL exit-4 on the Fitlet CeleronJ6413, then adds CPU-based RPP fallback and dependency. Captured CPU flags have neither AVX nor AVX2, and deployed navigation blob has the selection logic. This preserves a historical field failure/fix report; it is not a current physical go-to PASS. Reconcile before deployment and verify installed effective controller without moving first. Explicit MPPI on non-AVX is refused; unreadable CPU flags default to MPPI, a documented source limitation requiring readiness review.
- Gitb4f6a48 reports standing Auto stepping telemetry vx.01/vy−.03 causing roughly1.5m/min idle EKF/SLAM drift/map smear. The fix sets odom twist zero and holds dead-reckoned pose after default.5s without a bridge nonzero command (>1e-3). This is a historical field report plus inspected code/test fix, not our physical observation. Handheld walking bypasses command tracking and consequently can read still; suppression is not an independent motion sensor. Reconcile the fix/limitation explicitly, never silently discard it by deploying the integration branch.

Site caps2/1.5/2 and odom_sign[1,1,1] differ from integration defaults. Captured site configuration is evidence only, not calibrated acceptance or authorization to adopt those values. Legacy exporter domain0 versus SABLE23 can explain stale status in principle, but is not proven sole cause. Exporter lateral=true is advertised code capability, never body-y physical proof. Current historical Home_Map results do not establish acceptance for the captured SLAM launch.

## Minimum individually recorded physical retest matrix

This is a future evidence plan, **not authorization or an executable run**. Each exact physical run requires operator approval of limits/preflight/abort/evidence under the repository safety agreement. Record actual deployed SHA+resolved module hashes, effective limits/sign/scales/mode/firmware, owner/session, authoritative timestamped state/battery, input event, MQTT/ROS/vendor traces and synchronized physical observation. Define PASS/FAIL/ABORT before execution; any ownership uncertainty, stale state, competing writer, unexpected direction or stop failure aborts. First reconcile deployment CPU/idle-odom fixes and offline failures/gaps.

| Individual case | Minimum observed acceptance / preserved boundary |
|---|---|
| Stand | Explicit action from valid nonstanding state; zero motion; fresh state6 confirms standing; service reply alone not PASS |
| Sit | Explicit desired-down action, fresh lying confirmation; no replay of old drive; SDK Release is separate |
| Forward | Low approved vx+ pulse with packet sign/encoding and body-frame forward displacement; measured gain |
| Backward | Separate approved vx− pulse and physical direction/neutral; preserve asymmetric encoding |
| Yaw left | Separate wz+ pulse, physical counterclockwise yaw and wire inversion |
| Yaw right | Separate wz− pulse, clockwise yaw and wire inversion |
| Curve | Approved x+z combination, y0, trace actual motion and terminal neutral; not lateral proof |
| Strafe left | Investigate prior failure first; separate vy+ pulse with fixed body yaw/time-aligned lateral displacement; no world-y inference |
| Strafe right | Independent vy− run; no inference from the left run or vendor command existence |
| STOP | Stop while engaged and Stop while no local input; measure all-axis neutral delivery/latency/physical cessation |
| Deadman release | RB release while commanding; command disposal and physical stop; fresh RB required before next command |
| Command timeout | Controlled approved stream interruption; layered watchdog and physical stop timing; no resume from old input |
| MQTT/network reconnect | Held input during approved loss/recovery; no motion before valid new ownership+neutral+fresh RB; old session cannot revive |
| Controller disconnect | Selected Xbox USB/BLE/poll dropout separately as applicable; release/revoke/no motion; reconnect with held RB cannot drive |
| Ownership takeover | Competing client/session drives and body commands rejected during lease; release remains fail-safe; no hidden joystick/nav velocity |
| Manual from autonomy | Approved autonomy cancellation/takeover; lease claim has zero motion, nav/joy blocked; release/expiry does not resume autonomy |
| Fresh autonomy resumption | Only explicit fresh successful autonomy request after manual hold unlocks; old/failed request cannot unlock |
| Stale/unknown state | Approved safe fault-injection evidence plan after inert testing; zero and held latch; recovered telemetry does not replay old input |
| Low/unknown battery | Safe simulated/inert condition first; known/unknown drive guard and recovery neutral; never drain battery for a test |
| Transport failure | Inert fault injection first; physical stop/delivery behavior only under approved safe containment; send success not controller ACK |
| Posture/mode intent invalidation | Old motion cannot survive transition/recovery; physical refusal while moving and virtual discard/cancel are different contracts |
| Idle odometry | Actual stationary observation after settle with zero command versus physical motion truth; independent movement/handheld caveat documented |
| CPU/controller readiness | Live-static no-motion inspection of effective RPP/compatible binary; no SIGILL/respawn; go-to physical acceptance is separate |

Historical failure, safe refusal, interrupted run and later PASS must remain separate records. Dedicated body-y acceptance remains open until those two signs have their own evidence; no current physical case is marked PASS here.

Primary NOMAD evidence paths (plaintext absolute paths; source files stay in their authoritative repository):

- /home/raz/Documents/NOMAD/docs/LITE3_INTEGRATION.md
- /home/raz/Documents/NOMAD/docs/LITE3_HISTORY_AUDIT.md
- /home/raz/Documents/NOMAD/api/services/control_leases.py
- /home/raz/Documents/NOMAD/api/services/control_agent.py
- /home/raz/Documents/NOMAD/ros2_ws/src/sable_patrol/sable_patrol/control_authority.py
- /home/raz/Documents/NOMAD/ros2_ws/src/sable_patrol/sable_patrol/mqtt_bridge_node.py
- /home/raz/Documents/NOMAD/ros2_ws/src/sable_bringup/config/twist_mux.yaml
- /home/raz/Documents/NOMAD/ros2_ws/src/sable_lite3_bridge/sable_lite3_bridge/lite3_bridge_node.py
- /home/raz/Documents/NOMAD/frontend/web/src/composables/useTeleop.ts
- /home/raz/Documents/NOMAD/frontend/web/src/composables/useLaptopXbox.ts
- /home/raz/Documents/NOMAD/frontend/web/src/composables/laptopXbox.ts
- /home/raz/Documents/NOMAD/ros2_ws/src/sable_navigation/sable_navigation/kinematic_base_node.py

## Subsequent safe source closure — 2026-10-02

The read-only deployed snapshot remains unchanged. CPU-compatible controller selection and dispatch-bound idle odometry have subsequently been reconciled through existing SABLE owners, with offline tests only (TEST-20261002-106 / FINDING-20261002-095). Driver scaling diagnostics, bounded forwarding, UI evidence and passive validation preparation add observability without calibration changes. These are not deployed or physically proven. Direct strafe remains UNVALIDATED. See SAFE_AUTONOMOUS_CLOSURE.md for current counts, checks and blockers. Five additional supervised records TEST-20261002-107..111 are PLANNED ONLY, no new historical experiments; each physical matrix item is evaluated individually.
