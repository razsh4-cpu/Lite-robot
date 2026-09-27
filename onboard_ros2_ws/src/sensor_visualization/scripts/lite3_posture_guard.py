#!/usr/bin/env python3
"""Read-only preflight/status guard for state-aware HIGH-LEVEL posture toggles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import time

STATE_DIR = Path("/run/lite3-control")
RUNTIME_UNIT = "lite3-high-level-runtime.service"
STATUS_RE = re.compile(
    r"enabled=(?P<enabled>true|false).*?forward=(?P<forward>[-+0-9.]+) "
    r"lateral=(?P<lateral>[-+0-9.]+) yaw=(?P<yaw>[-+0-9.]+).*?"
    r"robot_status=(?P<posture>\S+).*?telemetry_fresh=(?P<fresh>true|false).*?"
    r"command_source=(?P<source>\S+)")


def run(command, timeout=4):
    return subprocess.run(command, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, timeout=timeout,
                          check=False)


def read_state(name, default="UNKNOWN"):
    try:
        value = (STATE_DIR / name).read_text(encoding="utf-8").strip()
        return value or default
    except OSError:
        return default


def latest_runtime_status():
    result = run(["journalctl", "--no-pager", "-o", "cat", "--since",
                  "15 seconds ago", "-u", RUNTIME_UNIT])
    for line in reversed(result.stdout.splitlines()):
        match = STATUS_RE.search(line)
        if match:
            data = match.groupdict()
            for key in ("forward", "lateral", "yaw"):
                data[key] = float(data[key])
            data["enabled"] = data["enabled"] == "true"
            data["fresh"] = data["fresh"] == "true"
            return data
    return None


def snapshot():
    runtime_active = run(
        ["systemctl", "is-active", "--quiet", RUNTIME_UNIT]).returncode == 0
    telemetry = latest_runtime_status()
    source = read_state("COMMAND_SOURCE", "NONE")
    localization_state = read_state("LOCALIZATION_STATE", "UNAVAILABLE")
    localization_startup = read_state(
        "LOCALIZATION_STARTUP_STATE", "UNAVAILABLE")
    try:
        localization_score = float(read_state("LOCALIZATION_SCORE", "0"))
    except ValueError:
        localization_score = 0.0
    velocities_zero = bool(telemetry) and all(
        abs(float(telemetry[key])) <= 1e-6
        for key in ("forward", "lateral", "yaw"))
    return {
        "connected": runtime_active and bool(telemetry) and telemetry["fresh"],
        "high_level_healthy": runtime_active and bool(telemetry) and telemetry["fresh"],
        "telemetry_fresh": bool(telemetry) and telemetry["fresh"],
        "posture": telemetry["posture"] if telemetry else "unknown",
        "command_source": source,
        "motion_enabled": bool(telemetry) and telemetry["enabled"],
        "velocities_zero": velocities_zero,
        "forward": telemetry["forward"] if telemetry else None,
        "lateral": telemetry["lateral"] if telemetry else None,
        "yaw": telemetry["yaw"] if telemetry else None,
        "localization_state": localization_state,
        "localization_startup": localization_startup,
        "localization_confidence": localization_score,
        "timestamp": time.time(),
    }


def posture_is_down(posture):
    return posture in {"sitting", "down", "lying", "damping"}


def decision(status, action, allowed_source="NONE"):
    if not status["high_level_healthy"]:
        return False, "HIGH-LEVEL UNHEALTHY"
    if not status["telemetry_fresh"] or status["posture"] == "unknown":
        return False, "ROBOT STATE STALE"
    if action == "stand" and status["posture"] == "standing":
        return True, "ROBOT ALREADY STANDING"
    if action == "down" and posture_is_down(status["posture"]):
        return True, "ROBOT ALREADY DOWN"
    if status["command_source"] != allowed_source:
        return False, f"POSTURE BLOCKED: COMMAND_SOURCE={status['command_source']}"
    if status["motion_enabled"] or not status["velocities_zero"]:
        return False, "POSTURE BLOCKED: NON-ZERO OR ACTIVE MOTION"
    return True, "POSTURE TOGGLE READY"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("status", "preflight", "confirm"))
    parser.add_argument("action", nargs="?", choices=("stand", "down"))
    parser.add_argument("--allow-source", default="NONE")
    args = parser.parse_args()
    status = snapshot()
    code = 0
    message = "OK"
    if args.command in {"preflight", "confirm"}:
        if not args.action:
            parser.error("action is required")
        ok, message = decision(status, args.action, args.allow_source)
        if args.command == "confirm":
            achieved = (status["posture"] == "standing" if args.action == "stand"
                        else posture_is_down(status["posture"]))
            ok = status["high_level_healthy"] and status["telemetry_fresh"] and achieved
            message = (("ROBOT STANDING" if args.action == "stand" else "ROBOT DOWN")
                       if ok else f"POSTURE NOT CONFIRMED: {status['posture']}")
        code = 0 if ok else 3
    status.update({"ok": code == 0, "message": message})
    print(json.dumps(status, sort_keys=True))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
