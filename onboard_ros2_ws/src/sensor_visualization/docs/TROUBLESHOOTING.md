# Lite3 live troubleshooting runbook

This is the first-stop runbook for the HIGH-LEVEL Lite3 stack on robot
`robot_01`. It records the failures observed during the live Day-1/Day-2
sessions on 2026-09-26 and the shortest proven way to distinguish them.

## Fixed identities and safety invariants

- Development laptop: `raz-ThinkPad-P14s-Gen-2i`.
- Onboard Mini-PC: `abx-fit-001`.
- SSH: `abx@192.168.2.32`.
- Robot Motion Host Ethernet endpoint: `192.168.1.120`.
- The persistent HIGH-LEVEL runtime is the sole receiver on UDP `43897`.
- Command sources are exclusive: `NONE`, `LOCAL_XBOX`,
  `LAPTOP_XBOX`, or `AUTONOMY`.
- Never infer that the robot is offline from one ROS command. Check power,
  ping, SSH, services, direct DDS discovery, and topic freshness separately.
- Never start Nav2 motion while localization is below 80%, while the source is
  not `NONE`, or while telemetry, `/odom`, `/scan`, or TF is stale.
- Restarting localization does not command motion, but it discards the current
  AMCL particle state. A new short manual movement may then be required.
- Restarting the persistent HIGH-LEVEL runtime can interrupt heartbeat and can
  change the robot's safe posture. Do not restart it merely to repair DDS or
  localization while the robot is standing.

## First 60 seconds of diagnosis

Run these in order from the laptop.

```bash
ping -c 3 192.168.2.32
ssh -o ConnectTimeout=5 abx@192.168.2.32 hostname
ssh abx@192.168.2.32 \
  'systemctl is-active lite3-high-level-runtime.service \
   lite3-lidar.service lite3-localization.service lite3-nav2.service \
   lite3-laptop-xbox-source.service'
ssh abx@192.168.2.32 \
  'for f in /run/lite3-control/{COMMAND_SOURCE,LOCALIZATION_STATE,LOCALIZATION_SCORE,HIGH_LEVEL_RUNTIME_READY,TELEMETRY_FRESH,ODOM_READY,LIDAR_READY,TF_READY}; do printf "%s=" "$f"; cat "$f" 2>/dev/null || echo MISSING; done'
```

Then bypass the ROS daemon cache and test current DDS discovery:

```bash
ssh abx@192.168.2.32 "bash -lc \
  'source /opt/ros/jazzy/setup.bash
   source /home/abx/ros2_ws/install/setup.bash
   export ROS_DOMAIN_ID=0 ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
   timeout 10s ros2 node list --no-daemon'"
```

If that omits the robot runtime or LiDAR, immediately repeat with UDP-only
Fast DDS transport:

```bash
ssh abx@192.168.2.32 "bash -lc \
  'source /opt/ros/jazzy/setup.bash
   source /home/abx/ros2_ws/install/setup.bash
   export ROS_DOMAIN_ID=0 ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
   export FASTDDS_BUILTIN_TRANSPORTS=UDPv4
   timeout 10s ros2 node list --no-daemon'"
```

Expected core nodes include `/lite3_high_level_runtime` and
`/sllidar_node`. If they appear only in the second command, use the Fast DDS
recovery section below. Do not restart the robot runtime first.

## Symptom index

| Symptom | Most likely cause | First check |
|---|---|---|
| SSH and ping both fail | Mini-PC off, battery exhausted, or network absent | Router client list and Mini-PC power |
| `connect joystick` says `robot_status` missing | Mini-PC/C2 service offline or DDS discovery failure | Ping, then robot-side C2 service |
| `status` says `ROBOT OFFLINE` while ping works | The status process cannot discover ROS graph | Direct node list with and without UDP-only transport |
| Services active but new ROS nodes see no `/scan` or `/odom` | Fast DDS shared-memory/discovery fault | UDP-only direct discovery test |
| Localization remains exactly 55.1% | Wrong AMCL hypothesis; stationary global search exhausted | Guard log and short manual movement |
| `/reinitialize_global_localization` never replies | AMCL/lifecycle executor is unresponsive | Localization journal; restart localization only |
| Localization restarts forever in `start-pre` | Input gate cannot discover scan/odom/TF | Run input gate manually with UDP-only transport |
| Localization becomes 0% after restart | AMCL particle history was reset | Wait, then short manual rotation/translation |
| Nav2 is `inactive` | Expected manual safety policy, or localization gate not met | Localization >=80% and unit journal |
| APT cannot resolve `packages.ros.org` | DNS/default-route failure, not a ROS package error | `getent hosts packages.ros.org` |
| Only Stand works from Xbox | Fresh manual authorization/standing gate missing | Center sticks, inspect runtime reason, use RB if already standing |
| Controller reconnects but motion does not resume | Intended fail-safe cleared authorization and cached motion | Reacquire source and perform a fresh authorization |
| Telemetry is bursty or callbacks starve | UDP receive loop drained without a bound | Verify bounded 64-datagram bridge version |
| Nav2 `/cmd_vel` appears missing | QoS mismatch between Nav2 and AUTONOMY source | Confirm sensor-data/best-effort QoS on both ends |

## Incident: Mini-PC or robot battery exhausted

Observed behavior:

- `192.168.2.32` stopped answering.
- C2 reported missing `robot_status`.
- The physical robot dropped to its safe lying posture when its battery ended.

Diagnosis:

```bash
ping -c 2 -W 1 192.168.2.32
ssh -o BatchMode=yes -o ConnectTimeout=5 abx@192.168.2.32 hostname
```

If both fail, stop ROS/C2 diagnosis. Power and network must return first.
Do not reinterpret a powered-off Mini-PC as a C2 software regression.

After power returns, the expected hostname is exactly `abx-fit-001`. Recheck
all services because a fresh boot invalidates earlier localization and command
source observations.

## Incident: Nav2 package installation failed with DNS errors

Observed error:

`Could not resolve 'packages.ros.org'`

This is a network/DNS failure. It does not prove that Nav2 packages or the APT
repository are invalid.

```bash
ip route
getent hosts packages.ros.org
resolvectl status
```

Only repeat `apt update` or package installation after DNS resolves. Do not
change package names, ROS distribution, or repository configuration merely
because DNS was unavailable.

## Incident: C2 status topic missing

Required topic:

`/c2/robot_01/laptop_xbox/robot_status`

Robot-side service:

`lite3-laptop-xbox-source.service`

Checks:

```bash
ping -c 1 -W 1 192.168.2.32
ssh abx@192.168.2.32 \
  'systemctl status lite3-laptop-xbox-source.service --no-pager'
systemctl --user status lite3-c2-xbox.service --no-pager
```

Both machines use `ROS_DOMAIN_ID=0` and
`ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET`. The robot service also needs
`/run/lite3-control` permissions created at boot. If ping fails, report
`ROBOT OFFLINE`; do not wait on ROS topic introspection.

`connect joystick` validates the local input device and then acquires
`LAPTOP_XBOX` for the selected robot. It never sends Stand or non-zero
motion. Reconnect never restores old authorization or velocity.

## Xbox authorization and posture

The current HIGH-LEVEL bridge behavior is:

- Centered `A` rising edge sends the vendor SIT/STAND toggle. It is not a
  state-aware "stand only" command, so pressing A while standing can make the
  robot lie down.
- If the robot is already standing, centered `RB` rising edge grants fresh
  manual authorization without a posture toggle.
- RB is an authorization edge, not a hold-to-run deadman.
- Source change, disconnect, stale joystick data, or reconnect clears manual
  authorization and cached motion.
- The 300 ms stale-command timeout remains mandatory.

Before touching a button, read the live robot state and command source. Never
press A repeatedly. Use RB once when the robot is already standing.

## Saved-map localization below 80%

Production gate:

- `LOCALIZATION_SCORE >= 0.80`.
- Three consecutive valid samples are required.
- Below the gate the system must report `UNLOCALIZED`; AUTONOMY/Nav2 motion
  remains blocked.

A saved pose is only an initial hypothesis. It is not proof that the robot is
physically at that pose. A real observed failure held at:

- score `0.551`;
- `216/392` scan wall hits;
- reason: stationary global search exhausted.

Correct sequence:

1. Load `Home_Map`.
2. Let AMCL try the saved hypothesis.
3. Trigger one global relocalization if still below 80%.
4. If the stationary search is exhausted, manually rotate about 20 degrees and
   translate 20-30 cm using the Xbox.
5. Release manual control.
6. Require three consecutive readings at or above 80%.

Do not remap, edit `Home_Map`, alter map origin, change LiDAR extrinsics, or
overwrite the saved pose to hide a low score.

## Incident: AMCL global-localization service hung

Observed behavior:

- The localization guard continued publishing the same 55.1% score.
- `/scan` was near 10 Hz and `/odom` was near 50 Hz.
- `/reinitialize_global_localization` printed "making request" but never
  returned.
- Lifecycle queries and `/amcl_pose` also failed to respond.

This indicates an unresponsive AMCL/lifecycle process, not stale sensors.
Restart only `lite3-localization.service`. Do not restart the persistent
HIGH-LEVEL runtime.

A localization restart resets AMCL state. Movement performed before the
restart no longer helps the new particle filter; another short manual movement
may be needed after AMCL is active.

## Incident: Fast DDS shared-memory discovery failure

This was the key restart failure observed on 2026-09-26.

Evidence:

- HIGH-LEVEL runtime and LiDAR processes were active.
- Existing laptop subscribers could still see traffic.
- A newly created robot-side DDS participant saw only C2/game-controller
  nodes, and the localization input gate saw no `/scan`, `/odom`, or TF.
- The same direct discovery command with
  `FASTDDS_BUILTIN_TRANSPORTS=UDPv4` immediately saw
  `/lite3_high_level_runtime`, `/sllidar_node`, camera, and C2 nodes.
- Running the deployed input gate manually with UDP-only transport returned:

```text
{"ready": true, "scan": true, "odom": true,
 "odom_base": true, "base_lidar": true}
```

Minimal fix:

- Export `FASTDDS_BUILTIN_TRANSPORTS=UDPv4` in
  `lite3_ros_inputs_ready.py`.
- Set the same environment in `lite3-localization.service` and
  `lite3-nav2.service`.
- Restart localization only; do not restart HIGH-LEVEL robot communication.

The source tree contains these changes. At the end of the incident session the
updated input-gate executable had been copied to the Mini-PC and localization
recovered. The two updated systemd unit files had not yet been installed
because the sudo timestamp expired. Do not call this persistence complete
until the install commands in "Pending deployment" succeed.

## Incident: misleading health output

The laptop `status` command once printed `ROBOT OFFLINE`, 0% localization,
and failed sensors while:

- ping and SSH succeeded;
- remote `/scan` was near 10 Hz;
- remote `/odom` was near 50 Hz.

Treat this combination as DDS discovery failure in the status process. Check
direct DDS discovery with and without UDP-only transport before changing robot
services. Health files under `/run/lite3-control` can also be stale across a
failed service restart; correlate them with journal timestamps and live topics.

## Telemetry and AUTONOMY transport fixes already prepared

The HIGH-LEVEL telemetry callback now:

- reads a bounded burst of at most 64 UDP datagrams;
- keeps the newest valid RobotState;
- publishes once per callback at the intended rate;
- cannot spin forever while datagrams keep arriving.

The AUTONOMY `/cmd_vel` input and protected output, plus the runtime
subscription, use sensor-data/best-effort QoS. This avoids a Nav2-to-AUTONOMY
QoS mismatch while preserving the 300 ms watchdog and exclusive lease.

These changes passed the focused offline regression suite. Revalidate
zero-only continuity live before the first physical autonomous goal.

## Nav2 service policy

`lite3-nav2.service` is deliberately not enabled for unconditional motion at
boot. `inactive` can therefore be the correct safe state. Start it only after:

- robot is standing;
- `COMMAND_SOURCE=NONE`;
- telemetry, `/odom`, `/scan`, TF, and `/lite3/battery_percent` are fresh;
- robot battery is at least 25%;
- localization has three consecutive samples >=80%;
- the dry path and costmaps look safe.

Starting Nav2 servers must not itself acquire AUTONOMY or send motion. The
physical goal still requires explicit operator approval.

## Pending privileged deployment from the 2026-09-26 incident

The source, launch files, and service definitions contain the UDP-only Fast
DDS fix. The installed `/etc/systemd/system` copies on the Mini-PC may still
be older because the sudo timestamp expired during the incident. The
non-privileged staging helper copies/builds the exact workspace files and
stages the units without starting or stopping anything:

```bash
/home/raz/ros-robot-cc/operator/stage_dds_runtime_fixes.sh
```

It prints the single attended sudo command needed to install the staged unit
files. The root step deliberately performs only `install` and
`daemon-reload`: it does not restart the HIGH-LEVEL runtime, localization,
Nav2, AUTONOMY, or publish any command. Use a controlled reboot/startup after
installation rather than restarting robot services piecemeal.

## Resume checklist after an interrupted session

1. Confirm physical posture and battery with the operator.
2. Confirm `COMMAND_SOURCE`; never assume a previous release succeeded.
3. Confirm HIGH-LEVEL runtime and the single UDP 43897 owner.
4. Confirm `/scan`, `/odom`, and TF freshness.
5. Confirm `/lite3/battery_percent` is fresh and at least 25%; low or unknown battery blocks AUTONOMY.
6. If new DDS participants see nothing, run the UDP-only discovery test.
7. Confirm `Home_Map` and localization gate.
8. If AMCL was restarted, expect a new short manual localization movement.
9. Release manual control and verify `COMMAND_SOURCE=NONE`.
10. Start Nav2 servers, perform a dry path, and request explicit approval before
   any physical goal.

## Last known state when this record was written

- The physical robot battery was exhausted; do not assume posture or readiness
  on the next power-on.
- Immediately before power loss localization was stable at 98.4--98.9% for 12
  consecutive samples after forcing new Fast DDS participants to UDPv4.
- A dry 10 cm Nav2 path succeeded (`GridBased`, three poses, error code 0).
  This was planning only; the robot did not execute it.
- The last verified arbitration state was `COMMAND_SOURCE=NONE` and
  `lite3-autonomy-command-source.service=inactive`.
- `lite3-nav2.service` was active, and one UDP 43897 receiver (PID 1196 at the
  time) was verified. PIDs and service states must be checked again after
  power-on; they are historical evidence, not current readiness.
- No physical autonomous motion was sent during the incident.


## Next powered session: shortest safe Day-2 path

Run these from a normal laptop terminal after the Mini-PC is reachable:

1. `prepare-day2` -- copies/builds the current tested files and installs the
   staged systemd units. It does not start services or send motion.
2. Reboot the Mini-PC in a controlled way, then verify the persistent runtime,
   sole UDP 43897 receiver, `/odom`, `/scan`, and TF.
3. Select `Home_Map`; require three consecutive localization samples >=80%.
   If stationary global localization cannot disambiguate, perform only the
   requested short manual rotation/20--30 cm motion.
4. Confirm fresh `/lite3/battery_percent` >=25%, clear test space, and
   `COMMAND_SOURCE=NONE`; then start `lite3-nav2.service`.
5. Run `day2-ready`. It is read-only and must print Nav2 ready, the measured
   localization confidence, battery percentage, and `COMMAND_SOURCE=NONE`.
6. Preview the 10 cm path on `/day2/preview_goal`. The Day-2 goal tolerance is 5 cm, so this test cannot pass without meaningful displacement. Only after visual review and
   explicit approval may AUTONOMY be acquired and a real goal be submitted.

The safety monitor revokes AUTONOMY for stale `/odom`, `/scan`, localization,
`/cmd_vel`, or battery data, localization below 80%, battery below 25%, or a
command beyond the Day-2 velocity limits.
