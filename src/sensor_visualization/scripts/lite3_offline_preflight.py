#!/usr/bin/env python3
"""Read-only Lite3 software/hardware readiness report; never sends UDP."""

import argparse
from pathlib import Path
import subprocess


WORKSPACE = Path("/home/abx/ros2_ws")


def command(*args):
    result = subprocess.run(args, text=True, capture_output=True, check=False)
    return result.returncode, (result.stdout + result.stderr).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live-network", action="store_true",
        help="also run route and ICMP reachability checks (never robot commands)")
    args = parser.parse_args()
    checks = {}
    checks["build_installed"] = (
        WORKSPACE / "install/sensor_visualization/lib/sensor_visualization/"
        "lite3_manual_axis_control").exists()
    checks["launch_installed"] = (
        WORKSPACE / "install/sensor_visualization/share/sensor_visualization/launch/"
        "lite3_xbox_vendor_gait.launch.py").exists()
    checks["xbox_js0"] = Path("/dev/input/js0").exists()
    checks["lidar_serial"] = Path("/dev/serial/by-id").exists()
    carrier = Path("/sys/class/net/enp3s0/carrier")
    checks["ethernet_carrier"] = carrier.exists() and carrier.read_text().strip() == "1"
    _, sockets = command("ss", "-lunp", "sport = :43897")
    checks["telemetry_port_free"] = "43897" not in sockets
    _, processes = command(
        "pgrep", "-af",
        "lite3_validation_console|xbox_lite3_motion_host_bridge|lite3_transfer")
    checks["no_competing_control_process"] = not bool(processes)
    launch_text = (WORKSPACE / "src/sensor_visualization/launch/"
                   "lite3_xbox_vendor_gait.launch.py").read_text()
    checks["transmit_defaults_false"] = 'default_value="false"' in launch_text
    if args.live_network:
        route_rc, route = command("ip", "-4", "route", "get", "192.168.1.120")
        ping_rc, ping = command("ping", "-c", "1", "-W", "1", "192.168.1.120")
        checks["robot_route_via_enp3s0"] = route_rc == 0 and "dev enp3s0" in route
        checks["robot_ping"] = ping_rc == 0
    for key, value in checks.items():
        print(f"{key.upper()}={'YES' if value else 'NO'}")
    software_keys = (
        "build_installed", "launch_installed", "telemetry_port_free",
        "no_competing_control_process", "transmit_defaults_false")
    print("SOFTWARE_READY=" + (
        "YES" if all(checks[key] for key in software_keys) else "NO"))
    print("ROBOT_COMMANDS_SENT=0")


if __name__ == "__main__":
    main()
