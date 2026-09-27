# Lite3 Day-2 physical test sequence

All tests require a charged, standing robot, clear emergency-stop access, fresh
telemetry/scan/odom, `NAVIGATION_READY` from three consecutive localization
samples >=80%, and `COMMAND_SOURCE=NONE` before the approved run. No test starts
without the operator's explicit approval.

## Test 1 — 10 cm straight

1. Preview a goal 0.10 m forward on `/day2/preview_goal`; inspect the path only.
2. Confirm footprint and both costmaps are clear.
3. After approval, acquire `AUTONOMY` and send that goal.
4. PASS: action succeeds, forward displacement is 0.05–0.15 m, lateral error is
   <=0.05 m, yaw change is <=10 degrees, and localization stays >=80%.
5. FAIL/ABORT: unexpected lateral/rotational motion, stale scan/odom/telemetry,
   localization <70% immediately, localization <80% for at least the existing
   2 s grace period, command-source change, low battery, or no progress for 3 s.

## Test 2 — 0.5–1.0 m plus turn

1. Preview a collision-free goal 0.5–1.0 m away with 20–45 degree final heading.
2. After approval, execute at the existing conservative limits.
3. PASS: goal succeeds within 0.10 m and 15 degrees; no footprint collision;
   localization remains >=80%.
4. Use the same immediate abort conditions as Test 1.

## Test 3 — obstacle response (chair at constrained clearance)

1. Place the chair approximately 0.20 m ahead and do not acquire AUTONOMY yet.
2. Confirm the chair is visible in the live red LiDAR scan and represented in
   both relevant costmaps.
3. Ask Nav2 for a short path that clears the inflated Lite3 footprint. Never
   shrink the 0.610 x 0.370 m footprint or its safety/inflation clearance.
4. If start clearance is already unsafe or no collision-free path exists,
   report `NO SAFE PATH — OBSTACLE TOO CLOSE` and do not move. This safe refusal
   is a PASS for obstacle protection.
5. If a safe path exists, show it first and wait for explicit approval. Execute
   only the minimum movement needed to clear the chair slightly, then STOP.
6. PASS: safe refusal, or a collision-free short detour with visible
   LiDAR-to-costmap response and no contact. FAIL: the chair is absent from the
   sensor/costmap, a path crosses the inflated footprint, or motion begins
   without approval. ABORT immediately for contact risk, stale scan/odom/
   telemetry, localization <70%, localization <80% beyond 2 s, ownership
   change, or any command outside configured limits.

Emergency stop: `operator/day2_stop.sh`. It stops the lease-owning AUTONOMY
adapter; the 300 ms command watchdog then enforces zero/release.
