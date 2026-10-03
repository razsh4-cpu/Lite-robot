# Independent NavigationPort implementation plan

Implements the approved independent-backend request, continuing commit 1c39dfb.
No deployment or hardware execution is authorized by this plan.

1. Test goal acceptance/rejection, Nav2 terminal results, cancellation timeouts,
   late goal acceptance, service ownership exclusion, release and zero confirmation
   with fake action transport and fixture system commands. Implement a bounded
   NavigationPort with a lazy-import ROS NavigateToPose transport.
2. Reuse the existing AUTONOMY systemd unit (no ownership-file writes), and the
   existing posture guard's read-only status for standing/zero confirmation.
   Never publish velocity. Partial/failed cancellation blocks subsequent goals.
3. Compose this port with existing saved-goal/patrol/alert orchestration. Reuse
   existing Nav2 preflight plus authoritative localization measurement files
   and sensor/odom/TF checks. Keep map identity external and checked against
   active Map Server assets and the actually loaded occupancy grid.
   Require explicit execution approval; default construction is read-only.
4. Run only focused backend/mission/operator/static tests. Preserve known ROS
   dependency limitations; use fake Nav2 rather than claim live validation.
5. Review changed paths, document no-motion verification and shortest supervised
   validation, commit backend-only changes. No push, frontend or Xbox changes.

Review focus: ambiguous sends must retain their handles; cancel acknowledgement
is not completion; safe zero must be observed, not assumed; foreign ownership
must never be released by this backend; map identity and readiness must not be
silently substituted when transitioning between patrol/alert goals.
