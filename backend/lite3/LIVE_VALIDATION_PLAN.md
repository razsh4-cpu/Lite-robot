# Independent no-motion integration candidate

Base: autonomy `5493827f2d222df1ae26930d4f459a01e597a0a2`.
Observed runtime: immutable deployed bundle `fc2e73458e7de1fdd10440bd2bd380c39ae8cdd8`
under `/home/abx/NOMAD/var/lite3-independent-runtime/`. The directory name is
provenance, not a NOMAD/SABLE runtime dependency. Its existing HIGH-LEVEL and
relay are retained without modification; no Xbox branch is merged.

1. Inspect installed graph/units/INERT parameters and map hashes read-only.
2. Stage only backend, generic mission contract, localization package and the
   necessary existing navigation/sensor scripts/configs; build only localization.
3. Verify imports, boundary logic, package discovery, local shell syntax/tests.
4. Operator sudo stops the unexpectedly active SABLE application and starts
   navigation-only service plus existing safety monitor. No HIGH-LEVEL restart,
   AUTONOMY unit installation/acquisition or transmit setting change.
5. Verify live scan/odom/TF/map/AMCL/gate/Nav2/costmaps, construct NavigationPort
   without sending; laptop RViz private preview only. Stop before motion.

Navigation controller output is `/autonomy_validation/cmd_vel`, not a physical
input. Generic `/goal_pose` is isolated from BT Navigator. Motion profile changes
are a separate future authorization; this validation unit conflicts with physical
AUTONOMY and SABLE. Existing runtime currently also conflicts with the legacy
AUTONOMY unit: that must be reconciled separately before any future acquisition.

Selected existing Home_Map is structurally valid only, not proven applicable to
the current physical site. Saved pose stays an initial hypothesis. The site
registry contains disabled unmeasured entries; no goal coordinates are invented.
Normal threshold remains 80% x3; visual alignment and real posture remain
independent physical checks. No GUI is installed or launched onboard.

Rollback: `sudo systemctl stop lite3-autonomy-validation.service lite3-nav2-safety-monitor.service`.
This stops navigation only, retains the independent runtime and leaves SABLE off.
