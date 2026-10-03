"""Independent onboard launcher. Default is read-only verification, not motion."""
import argparse
import json
from pathlib import Path
import sys
import time


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--goto", dest="goal")
    mode.add_argument("--patrol")
    mode.add_argument("--alert")
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 300:
        parser.error("timeout must be 1–300 seconds")
    import yaml
    site = yaml.safe_load(args.site.read_text())
    root = args.site.resolve().parent
    for name in ("map_yaml", "saved_goals"):
        if not isinstance(site.get(name), str) or not site[name]:
            parser.error(f"external site requires {name}")
    map_yaml, registry = (root / site[name] for name in ("map_yaml", "saved_goals"))
    # The existing generic mission package stays in its current source location.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "product/missions"))
    import rclpy
    from rclpy.node import Node
    from .runtime import create_ros_runtime
    rclpy.init()
    node = Node("lite3_independent_autonomy")
    runtime = None
    try:
        runtime = create_ros_runtime(node, registry, map_yaml, site.get("alerts", {}))
        deadline = time.monotonic() + min(args.timeout, 30)
        while not runtime.verify() and time.monotonic() < deadline:
            time.sleep(0.02)
        status = runtime.status()
        print(json.dumps(status, default=str, sort_keys=True))
        if not runtime.verify():
            print("AUTONOMY BLOCKED — " + str(runtime.blocker))
            return 2
        if not any((args.goal, args.patrol, args.alert)):
            print("LOCALIZATION/NAV2 READY — NO MOTION REQUESTED")
            return 0
        if args.goal:
            runtime.backend.goals.resolve(args.goal, runtime.observation.tracker.map_identity)
            proposal = {"goto": args.goal}
        elif args.patrol:
            route = site.get("patrols", {}).get(args.patrol)
            if not isinstance(route, list) or not 2 <= len(route) <= 3:
                raise ValueError("validation patrol needs 2–3 measured saved goals")
            for goal in route:
                runtime.backend.goals.resolve(goal, runtime.observation.tracker.map_identity)
            proposal = {"patrol": args.patrol, "route": route}
        else:
            target = runtime.backend.alert_routes.get(args.alert)
            runtime.backend.goals.resolve(target, runtime.observation.tracker.map_identity)
            proposal = {"alert": args.alert, "goal": target}
        print(json.dumps(proposal))
        print("Limits: vx 0.10 m/s, vy 0.05 m/s, wz 0.20 rad/s; bounded timeout", args.timeout)
        try:
            approved = input("Physical robot movement will occur. Continue? [y/N] ").strip().lower() == "y"
        except (EOFError, KeyboardInterrupt):
            approved = False
        if not approved:
            print("CANCELLED — NO OWNERSHIP OR MOTION REQUESTED")
            return 0
        # Re-evaluate live readiness after the operator took time to approve.
        runtime.navigation.authority.approved = True
        deadline = time.monotonic() + 10
        while not runtime.verify() and time.monotonic() < deadline:
            time.sleep(0.02)
        if not runtime.verify():
            print("AUTONOMY BLOCKED — " + str(runtime.blocker))
            return 2
        if args.goal: runtime.goto(args.goal)
        elif args.patrol: runtime.start_patrol(args.patrol, route)
        else: runtime.handle_alert(args.alert)
        deadline = time.monotonic() + args.timeout
        while runtime.backend.request_id and time.monotonic() < deadline:
            runtime.step()
        if runtime.backend.request_id:
            runtime.cancel_navigation()
            print("BOUNDED TIMEOUT — STOP REQUESTED")
            return 3
        print(json.dumps(runtime.status(), default=str, sort_keys=True))
        return 0 if runtime.backend.navigation_state == "ARRIVED" else 4
    finally:
        if runtime and runtime.backend.request_id:
            if not runtime.cancel_navigation():
                print("STOP UNCONFIRMED — KEEP AUTONOMY DISABLED; OPERATOR CHECK REQUIRED", file=sys.stderr)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
