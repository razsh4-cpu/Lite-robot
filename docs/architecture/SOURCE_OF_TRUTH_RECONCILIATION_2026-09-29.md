# Source-of-truth reconciliation — 2026-09-29

## Scope and evidence

This record reconciles real source/configuration evidence from:

- Git destination `/home/raz/ros-robot-cc/Lite-robot`, starting at
  `9e9fea500b509f1cbb560eeddd49106b37b7babd`;
- laptop development copies under `/home/raz/ros-robot-cc/onboard_ros2_ws` and
  `/home/raz/ros-robot-cc/operator`;
- read-only Mini-PC source and installed-unit evidence from
  `abx@192.168.2.32`.

The Mini-PC was never modified, restarted, deployed to, or sent ROS/UDP/motion
commands during reconciliation. Content hashes and consumers were used instead
of timestamps. Build/install/log/cache/runtime-state files were excluded.

## Approved authority decisions

| Area | Authority | Decision |
|---|---|---|
| Localization test override | Mini-PC/deployed safety bound merged with Git implementation | Keep the Git session-scoped override design, but use a single 180-second maximum/default in the token producer and independent localization consumer. Normal navigation remains 80% ×3. |
| LOCAL_XBOX production unit | Mini-PC/deployed | `lite3-local-xbox-control.service` depends on `lite3-xbox.service` and does not inject an ONNX policy path. It remains optional, explicitly selected and lease-gated. |
| Health/readiness | Git | Keep lifecycle-active Map Server/AMCL checks, corrected bounded TF probing, freshness checks and fail-closed diagnostics. |
| LiDAR startup unit | Git / installed unit | The installed unit hash exactly matches Git, while the Mini-PC source workspace copy is stale. |
| Obstacle-test install rule | Mini-PC source cleanup | Keep one executable install rule; remove the redundant second install of the same Python file. |

## Laptop development classification

The Git tree contains the latest intentional laptop development for the
obstacle-test CLI, temporary localization override, richer diagnostics, clean
RViz operator view, relocalization/AUTONOMY tests and headless startup docs.
The separate laptop `onboard_ros2_ws` is an older snapshot and is not an
authority where it lacks these features.

Installed laptop commands are split between Git and the historical external
`operator` directory. The installed `robot`, `maps`, `mapping`, `status` and
`relocalize` targets have content-identical Git counterparts. `commands` and
`nav` already resolve directly to the Git-controlled operator sources. The
external command registry and older chair/deploy helpers lack later generic
obstacle-test functionality and are not backported.

## Mini-PC/deployed classification

The deployed system is hybrid, so no complete Mini-PC tree is authoritative.
The installed HIGH-LEVEL, Nav2, localization, LiDAR and network-readiness units
match individual Git-controlled units even when a Mini-PC source workspace copy
does not. The deployed LOCAL_XBOX unit and 180-second override bound are the
specific recovered production decisions.

The low-level interfaces, command-source arbiter, Xbox gates, state machine and
most low-level tests are byte-identical between Mini-PC and Git. Mini-PC home
scripts that have Git counterparts are identical where present. Historical
`.orig`, `.pre_*`, build/install/log/cache files and `/run` state are not source.

## Legacy / R&D boundary

The root ONNX policy and low-level policy runner remain Advanced Locomotion /
Physical-AI R&D. They are not injected into the production LOCAL_XBOX service.
No R&D source or evidence is deleted by this reconciliation. Product manual
control remains lease-gated through the deployed LOCAL_XBOX behavior and the
persistent HIGH-LEVEL product boundary documented in the architecture baseline.

## Preserved safety invariants

- one persistent HIGH-LEVEL runtime and one UDP 43897 receiver;
- exclusive `NONE` / `LOCAL_XBOX` / `LAPTOP_XBOX` / `AUTONOMY` ownership;
- normal localization gate remains 80% ×3;
- test override is explicit, session-scoped, 70% ×3 and at most 180 seconds;
- service stop/failure/cancel restores normal localization policy;
- no deployed service or hardware state was changed during source recovery.
