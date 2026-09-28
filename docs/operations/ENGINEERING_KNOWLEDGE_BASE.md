# Engineering knowledge base

This is a compact record of consequential failures in the hardware-proven
Lite3 product path. It is not a chronological debug log. Evidence classes are
kept explicit; a prepared fix is not called proven until it has the required
live or physical validation.

## HIGH-LEVEL systemd-active but ROS-dead

- **Symptom:** `lite3-high-level-runtime.service` was `active`, while its ROS
  node, topics, telemetry, or DDS participant was absent.
- **Root Cause:** systemd process state was being treated as ROS health; startup
  and DDS recovery could leave a half-alive process graph.
- **Fix:** health now checks the ROS graph and fresh telemetry, with a bounded
  watchdog/restart path and network/DDS readiness ordering.
- **Regression Prevention:** boot acceptance must inspect actual topics, node
  presence, freshness and TF—not only `systemctl is-active`.
- **Status:** `IMPLEMENTED`; live software validated. Long-duration soak remains
  useful.

## Ghost command-source lease

- **Symptom:** `COMMAND_SOURCE=AUTONOMY` or another source remained observable
  after the owning process had failed or exited, blocking later acquisition.
- **Root Cause:** partial-failure cleanup did not always reconcile the state
  marker with the kernel lock/process liveness.
- **Fix:** safe cancel/recovery zeros through the existing source path, clears
  temporary authorization, releases ownership and restores `NONE`.
- **Regression Prevention:** exercise acquisition failure, process exception,
  repeated cancel and stale-marker recovery; never infer ownership from the
  marker alone.
- **Status:** `PARTIAL`; recovery was used live, but remains a priority
  regression target until all sources share parity-tested cleanup.

## `/odom` flooding

- **Symptom:** `/odom` and `odom→base_link` were emitted at approximately
  154 Hz, creating unnecessary executor/DDS load.
- **Root Cause:** all queued vendor telemetry datagrams were published rather
  than bounding the receive burst and publishing the newest state once per
  telemetry tick.
- **Fix:** the sole UDP receiver drains a bounded burst and publishes the newest
  valid state at a 20 ms cadence (maximum 50 Hz).
- **Regression Prevention:** assert single UDP `43897` ownership and bounded
  odometry/TF rate in runtime acceptance.
- **Status:** `IMPLEMENTED`; live software validated.

## AUTONOMY QoS stall

- **Symptom:** Nav2 produced velocity intent but the AUTONOMY adapter did not
  reliably receive it.
- **Root Cause:** incompatible ROS 2 QoS expectations on the velocity path.
- **Fix:** the Nav2-to-AUTONOMY subscription uses the compatible sensor-data /
  BEST_EFFORT policy while retaining validation and the 300 ms watchdog.
- **Regression Prevention:** integration-test publisher/subscriber QoS and
  require command freshness without sending hardware commands.
- **Status:** `IMPLEMENTED`; offline and live software validated.

## AMCL startup/lifecycle failure

- **Symptom:** Map Server/AMCL units appeared active, but lifecycle configure or
  activation timed out, `/amcl_pose` and `map→odom` were missing, and confidence
  remained zero.
- **Root Cause:** lifecycle transitions started before DDS, `/scan`, `/odom` and
  Map Server were actually ready; lost transition responses could leave a stuck
  stack.
- **Fix:** deterministic readiness sequence, bounded lifecycle retries, explicit
  stages, and localization-only restart after DDS participants are allowed to
  disappear.
- **Regression Prevention:** reboot acceptance verifies fresh inputs, lifecycle
  states, TF and confidence in order; `active` alone is insufficient.
- **Status:** `IMPLEMENTED`; offline and live software validated. Repeated-boot
  soak remains open.

## Wi-Fi `rtl8851bu` instability

- **Symptom:** the Mini-PC intermittently disappeared from SSH/network while
  Linux crash evidence was absent.
- **Root Cause:** strongest evidence is an out-of-tree `rtl8851bu` driver with
  kernel UBSAN array-index errors and concurrent station/AP-style interfaces.
- **Fix:** prepared network policy pins NetworkManager to the station interface,
  marks the AP interface unmanaged, disables Wi-Fi power saving and preserves
  `RobotDawg5.0` with static `192.168.2.32`.
- **Regression Prevention:** persistent reliability sampling plus repeated-boot
  and mission-load network soak.
- **Status:** `PARTIAL`; classified primarily as network loss, but the prepared
  fix is not closed until a long soak passes.

## Duplicate RViz instances/configuration

- **Symptom:** duplicate windows or restart paths restored unwanted overlays and
  inconsistent operator views.
- **Root Cause:** more than one launcher/watcher/config source could start or
  configure RViz.
- **Fix:** one canonical laptop RViz configuration and single-instance watcher;
  robot-side startup remains headless.
- **Regression Prevention:** close/reopen and reconnect acceptance checks exactly
  one RViz process and the canonical config path.
- **Status:** `IMPLEMENTED`; live operator view validated.

## NavFn yaw/footprint diagnostic bug

- **Symptom:** an independent clearance checker reported false collision or
  zero clearance on curved NavFn paths.
- **Root Cause:** candidate poses commonly contained `yaw=0`; the checker treated
  it as body orientation instead of deriving path tangent.
- **Fix:** derive orientation from the local path tangent after the start pose.
- **Regression Prevention:** regression fixture covers zero-yaw curved NavFn
  paths and compares the oriented rectangular footprint.
- **Status:** `IMPLEMENTED`; offline regression tested and used in dry planning.

## Mini-PC power interruption during autonomous navigation

- **Symptom:** an avoidance run moved around the chair but power/link loss
  interrupted evidence before terminal arrival/release could be established.
- **Root Cause:** external power/cable interruption; no software root cause was
  proven from that run.
- **Fix:** later accepted run used a stable power arrangement and completed the
  existing stop/release chain.
- **Regression Prevention:** physical test preflight includes battery/power,
  cable freedom, abort capability and evidence capture; interrupted runs never
  count as PASS.
- **Status:** `MITIGATED`; hardware power robustness remains operational debt.

## Obstacle investigation lacked a reconstructable snapshot

- **Symptom:** an offline review could not identify the exact 8 mm clearance
  pose/cell after the live chair dry run.
- **Root Cause:** the required scan, both costmaps, TF, candidates and
  per-pose clearance evidence had not all been preserved together.
- **Fix:** the built-in obstacle test now writes a bounded session snapshot with
  the live inputs, every candidate, selected path, footprint/settings and
  limiting cell.
- **Regression Prevention:** dry planning tests assert inert behavior and the
  required evidence fields; interrupted or incomplete sessions are not PASS.
- **Status:** `IMPLEMENTED`; offline regression tested; next live obstacle run
  must confirm the installed artifact set.

## Obstacle-test Python helper was executable but not importable

- **Symptom:** `lite3_nav2_preflight` could execute the override helper but
  `from lite3_nav_test_override import read` failed after a clean install.
- **Root Cause:** CMake installed only an extensionless renamed executable, not
  an importable `lite3_nav_test_override.py` module.
- **Fix:** CMake installs both the operator executable and the `.py` module in
  the package library directory. No manual install-tree copy is required.
- **Regression Prevention:** static packaging test requires both install rules;
  deployment performs a clean package build.
- **Status:** `IMPLEMENTED`; offline regression tested; Mini-PC clean-build
  import remains a deployment validation item.

## Wrong saved map selected for localization/test

- **Symptom:** scan quality appeared stable near 75–79%, but localization did
  not reach the normal gate and the planned obstacle test referenced the old
  `Home_Map` rather than the newly mapped environment.
- **Root Cause:** operator/test preflight did not make the active map identity
  sufficiently prominent before interpreting confidence.
- **Fix:** obstacle-test status/preflight records and displays the active map
  YAML; the runbook requires selecting the intended existing map before any
  threshold or planning decision.
- **Regression Prevention:** never tune AMCL or use a test override until active
  map identity is verified; snapshots preserve the map reference.
- **Status:** `IMPLEMENTED` in tooling/documentation; requires live deployment
  verification with the intended map.
