# Next steps

## 1. One bounded ICP-recovery mapping run

Battery preferably >35%, fresh state 6, one controller, E-stop, clear area.
Start passive LiDAR/ICP/SLAM, verify `/scan`, `/odom`, `/map` and TF, start one
vendor-gait control chain, record a bag, execute one short forward action, then
neutral. Verify positive-X and recovery after any isolated ICP rejection. Stop
and analyze; never auto-retry.

## 2. Save/validate map

Reject maps with jumps, duplicated walls or scale/orientation errors. Record the
commit/config with the saved map. Validate stationary AMCL before planning.

## 3. Planning only

Measure footprint and sensor extrinsic accurately. Run AMCL/planner/costmaps
without controller output and validate in RViz.

## 4. First autonomous motion

Only then route Nav2 `/cmd_vel` through the existing arbiter/deadman/vendor-gait
adapter for one bounded supervised goal.

Later: D455/person detection, mission manager and package split.

