# MINI-PC DEPLOYED-STATE AUDIT

Audit date: 2026-10-02. Host: `abx@192.168.2.32` (`abx-fit-001`). This is a read-only snapshot, not a deployment or physical acceptance test. Reachability was checked first: two ping replies, zero loss, 2.264–3.964 ms RTT. SSH used existing host-key verification and batch authentication. No robot IP was probed.

## Evidence sources inspected

Read-only Git branch/status/SHAs; filesystem paths, symlinks, hashes and timestamps; installed ROS package inventory; approved systemd state/configuration fields; explicit environment/YAML allowlists; CPU instruction flags; network interface/route metadata; bounded journal event aggregates without message text; `/proc` fixed-name process and UDP binding counts; map YAML and bag metadata; platform-status numeric/enum allowlists; service-backup archive member names. No bag payload was copied or replayed. No robot code was imported or executed.

Durable non-secret facts: [allowlisted snapshot](evidence/MINIPC_READ_ONLY_20261002.json). Additional local raw metadata inventories remain in `/tmp/lite3-final-audit`; they are not indiscriminately committed to the knowledge base. Their scope was capped (initial broad artifact scan 2,400 entries, targeted scan 1,122). This is best available inspected evidence, not a claim of exhaustive coverage of every file or journal.

## What actually ran versus repository source

| Layer | Observed deployed state | Current laptop integration | Consequence |
|---|---|---|---|
| SABLE checkout | `/home/abx/NOMAD`, tracked-clean `main`, `b4f6a48a56e96c524515d811abc92608ef1e1f3f` | `bipolix_robot`, `0c48b4d` integration closure | Different branches: neither supersedes the other merely by deployment |
| Active product services | Enabled/active `sable-edge`, `sable-ros`, `sable-edge-mosquitto`; local MQTT port1885 | Existing product API/network/ROS architecture retained | This is SABLE deployment, not historical standalone arbiter services |
| ROS launch | Jazzy, domain23, LOCALHOST discovery; Lite3, RPLIDAR S2, RealSense, SLAM, viz bridge; `/etc/sable/robot.yaml` override | Integration tested offline | Historical Home_Map/AMCL success does not validate current SLAM deployment |
| Network teleoperation | Deployed MQTT source lacks new `ControlAuthority` and startup manual-lock integration; deployed driver lacks new battery guard | New protected laptop Xbox lease/neutral/fresh engagement path exists locally | Current Request Control end-to-end acceptance cannot be assumed on this deployed version |
| Nav2 controller | Deployed source contains `141b497` CPU-based MPPI/RPP selection | Integration branch lacks this fix | CPU lacks AVX; deploying integration alone risks restoring known SIGILL failure |
| Still odometry | Deployed driver contains `b4f6a48` idle twist/pose suppression after0.5s without nonzero drive | Integration branch lacks this fix | Preserve/reconcile explicitly before deployment; handheld bypass caveat applies |
| Teleop limits | Site vx2.0, vy1.5, wz2.0;20Hz;deadman0.5s | Repo defaults vx0.5,vy0.3,wz0.6 | Higher site caps are configuration evidence, not proof or permission to adopt them |
| Driver limits/sign | Site max2/1.5/2, axis format, odom_sign[1,1,1], timeout0.4s | Repo sign[-1,1,1], lower defaults | Calibration/rationale UNKNOWN; review effective launch overrides before physical testing |
| Legacy status exporter | Enabled/active domain0; SABLE domain23 | Product readiness must come from authoritative current robot state | Possible domain blindness; not proven sole cause of exporter OFFLINE |
| Old Lite-robot source | Dirty `handoff/low-level-leg-control-2026-09-17`,25b9865 | Laptop clean feature/phase3c-teleop-v2,cc9cd69 | Old R&D files do not establish current product runtime |
| Old ROS workspace | Dirty main1f3331d; source/install aliases into Desktop/robotdog_ws | Historical retained scripts/config | Symlink aliases are not independent deployments or duplicate UDP writers |

The deployed YAML also sets general MQTT `command_ttl_sec=15.0`. This is not the teleop deadman: teleop remains0.5s and driver timeout0.4s in the captured override. The audit did not measure network latency or prove effective expiry of every command class.

### Installed-source provenance

Editable `.egg-link` installation resolves driver, MQTT adapter and navigation stack through build directories to `/home/abx/NOMAD/ros2_ws/src`. Their resolved hashes equal corresponding `b4f6a48` Git blobs:

- driver `aa6a61afc5838ef6846da14338bfdc36427172e05184bf570ef0978dfe8e5aad`;
- MQTT adapter `0e1af467010ebdc2ea51193434c2340eb5032ccd31766f896f4e724ead04b34b`;
- navigation stack `7433add9c096182bacbcf02c5120a89917bbf94e74b88a950ea495b932669218`.

Missing guessed site-packages `.py` files were explained by editable installs, not missing packages. Matching source/install resolution verifies available installed code; it does not inspect already-imported process memory. Build/running markers both865c671af4a035029cd7e7075d5188ec40f66a6d; build key0ba245cc842f1bbf5e595de1ee5d1f734455ef6c. These are updater-specific ROS content keys (exclude vision/pinned third-party handling), not full repository tree IDs. Their difference from the full Git tree is not independently a drift failure; the key was not recomputed by sourcing execution scripts on the Mini-PC.

## Important newly recovered deployment experiments

**CPU compatibility:** Nav2 go-to failed with SIGILL exit-4 and container respawn, according to primary Git commit141b497. The apt MPPI binary reportedly contained AVX instructions; the inspected J6413 has no AVX/AVX2. CPU-based RPP selection and dependency were added; deployed source contains the fix. Runtime controller and physical go-to retest were not performed by this audit. Carry forward hardware instruction compatibility as a readiness requirement.

**Idle odometry:** Primary Git commitb4f6a48 reports Auto gait stepping in place, telemetry vx0.01/vy−0.03 and approximately1.5m/min integrated drift/map smear. The fix holds pose/zero twist after0.5s without a nonzero bridge command. The deployed fix is present; integration branch lacks it. This is distinct from odometry publication flooding and ICP/TF failures. External handheld walking bypassing this bridge is a known limitation, not a validated motion sensor replacement.

## Useful retained artifacts

- September24 MCAP payloads are present: day1_1m_odom67,192,670bytes/150.149s and day1_amcl40,863,198bytes/89.301s. Metadata shows `/odom` approximately200Hz and `/scan` approximately10Hz; this does not prove one-metre travel, localization accuracy or motion safety.
- September15 ICP recovery, main recording and TF-forward metadata survive but referenced payloads are missing. Two offline-smoke metadata files contain zero messages and missing payloads. They cannot become PASS evidence.
- September24 bag rate (~200Hz aggregate) and September27 contemporary report (~154Hz) describe different captures. Do not collapse either into the unsupported recovered claim of1kHz, or assume deployed publication rate from historical metadata.
- `room_map`, `site_full_20260925`, and `Home_Map` YAML references survive at5cm resolution with distinct origins. Matching YAML does not establish matching occupancy pixels or current localization.
- October1 service backup archive retains historical Xbox/localization/Nav2/mapping/relocalization unit names. Units currently reported not-found/inactive are stale architecture evidence, not live control sources.
- Exporter source and editable-installed module hashes match, with process-group cleanup markers present. Older staging files differ. This supports presence of the child-cleanup fix, not a successful current reliability soak.
- `/run/lite3-control/COMMAND_SOURCE` absent, manual availability false; legacy status exporter reports OFFLINE/unknown ownership and advertises lateral support. Advertised capability constants are not physical proof; exporter cannot authorize NOMAD motion.
- One bound UDP43897 socket was observed. Port43893 had no bound listener; transmit sockets may be ephemeral, so this does not prove commands absent historically or receiver health.

## Stale/superseded artifacts and missing evidence

The October1 archive, R&D handoff checkout, old Desktop workspace and staging scripts preserve valuable history. Neither their presence nor timestamps proves they currently execute. Service start timestamps showed July28 despite current-date uptime of minutes: chronology has a clock/provenance discrepancy; cause UNKNOWN. Do not infer months of continuous uptime.

Full historical handoff exports and raw process/journal/socket text were blocked by automatic approval review because arbitrary bodies may contain secrets; safe metadata/allowlists were used. `/etc/sable/edge-mosquitto.conf` was permission denied and no privilege escalation was used to read it. Central broker destination/current bridge credentials and some retained document/log content therefore remain unverified. Secret-bearing configuration existence/purpose is recorded without credentials. Local Codex history was keyword-indexed, not exhaustively adjudicated as independent physical evidence.

No new physical retest, ROS graph/topic sampling, installed-process memory inspection, bag payload validation, current measured publish rate, localization acceptance, command-source acquisition or robot availability assertion was made. Domain mismatch is a plausible status inconsistency, not proven physical disconnection. Site sign/limits lack recovered calibration provenance.

## Implications for current SABLE/NOMAD

Keep laptop Xbox → NOMAD Request Control → protected network path as target. Mini-PC `/dev/input/js0` and LOCAL_XBOX are not readiness requirements. Before any future deployment, explicitly reconcile both branches' useful changes, preserve the CPU and idle-odometry fixes, review site caps/sign, and replace stale exporter assumptions with authoritative SABLE telemetry. This audit makes those dependencies reviewable; it performs no deployment or motion.

MINI-PC ACCESSED: READ ONLY

MINI-PC FILES MODIFIED: NO

SERVICES MODIFIED: NO

ROBOT OWNERSHIP ACQUIRED: NO

ROBOT COMMANDS SENT: NO

ROBOT MOTION: NONE (no motion commanded by this audit; physical motion was not independently monitored).
