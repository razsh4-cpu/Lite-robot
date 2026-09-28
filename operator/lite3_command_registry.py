#!/usr/bin/env python3
"""Single source of truth for installed Lite3 laptop operator commands."""

from __future__ import annotations

from dataclasses import dataclass
import shutil


@dataclass(frozen=True)
class Command:
    group: str
    command: str
    tag: str
    description: str
    executable: str


COMMANDS = (
    Command("ROBOT", "robot status", "READ ONLY",
            "Show connection, posture and robot state", "robot"),
    Command("ROBOT", "robot stand", "MOTION",
            "Safely stand Lite3 using the existing posture path", "robot"),
    Command("ROBOT", "robot down", "MOTION",
            "Safely lower Lite3 using the existing posture path", "robot"),

    Command("MANUAL CONTROL / C2", "connect joystick", "OWNERSHIP",
            "Connect Xbox, select a robot and request manual control", "connect"),
    Command("MANUAL CONTROL / C2", "disconnect joystick", "OWNERSHIP",
            "Safely release control and disconnect Xbox", "disconnect"),
    Command("MANUAL CONTROL / C2", "c2 select robot robot_01", "CONFIG",
            "Select robot_01 without sending motion", "c2"),
    Command("MANUAL CONTROL / C2", "take control", "OWNERSHIP",
            "Request LAPTOP_XBOX ownership for the selected robot", "take"),
    Command("MANUAL CONTROL / C2", "release control", "OWNERSHIP",
            "Send neutral and release LAPTOP_XBOX ownership", "release"),
    Command("MANUAL CONTROL / C2", "c2", "READ ONLY",
            "Show the equivalent grouped C2 command syntax", "c2"),

    Command("MAPS & LOCALIZATION", "status", "READ ONLY",
            "Show overall mapping and localization health", "status"),
    Command("MAPS & LOCALIZATION", "maps", "MOTION",
            "List/select a saved map; may offer approved relocalization", "maps"),
    Command("MAPS & LOCALIZATION", "maps Home_Map", "MOTION",
            "Select Home_Map directly; may offer approved relocalization", "maps"),
    Command("MAPS & LOCALIZATION", "mapping", "MODE CHANGE",
            "Enter SLAM mapping mode; never drives the robot", "mapping"),
    Command("MAPS & LOCALIZATION", "mapping --cancel", "MODE CHANGE",
            "Cancel mapping and restore prior localization", "mapping"),
    Command("MAPS & LOCALIZATION", "relocalize status", "READ ONLY",
            "Show relocalization, posture and localization state", "relocalize"),
    Command("MAPS & LOCALIZATION", "relocalize", "MOTION",
            "Preview and request an explicitly approved bounded recovery", "relocalize"),
    Command("MAPS & LOCALIZATION", "relocalize cancel", "SAFETY",
            "Stop recovery, command zero and release ownership", "relocalize"),

    Command("NAVIGATION & VALIDATION", "nav test obstacle", "MOTION",
            "Plan, approve and run a bounded obstacle-avoidance test", "nav"),
    Command("NAVIGATION & VALIDATION", "nav test obstacle status", "READ ONLY",
            "Show current/last obstacle-test and live preflight state", "nav"),
    Command("NAVIGATION & VALIDATION", "nav test obstacle cancel", "SAFETY",
            "Cancel Nav2, zero/release AUTONOMY and stop the test", "nav"),
    Command("NAVIGATION & VALIDATION", "day2-ready", "READ ONLY",
            "Run the Nav2 go/no-go preflight", "day2-ready"),
    Command("NAVIGATION & VALIDATION", "day1-acceptance", "READ ONLY",
            "Run the Day-1 health acceptance check and open RViz", "day1-acceptance"),
    Command("NAVIGATION & VALIDATION", "prepare-day2", "MAINTENANCE",
            "Deploy prepared Day-2 files; starts no motion", "prepare-day2"),

    Command("SYSTEM", "commands", "READ ONLY",
            "Show this operator command menu", "commands"),
)


GROUP_ORDER = (
    "ROBOT",
    "MANUAL CONTROL / C2",
    "MAPS & LOCALIZATION",
    "NAVIGATION & VALIDATION",
    "SYSTEM",
)


def available(command: Command) -> bool:
    # The menu itself is available while this process is executing, even if a
    # caller invokes it by absolute path during installation validation.
    return command.executable == "commands" or shutil.which(command.executable) is not None


def render() -> str:
    visible = tuple(command for command in COMMANDS if available(command))
    command_width = max(len(command.command) for command in visible)
    tag_width = max(len(f"[{command.tag}]") for command in visible)
    lines = ["# LITE3 OPERATOR COMMANDS"]
    for group in GROUP_ORDER:
        entries = [command for command in visible if command.group == group]
        if not entries:
            continue
        lines.extend(("", group))
        for entry in entries:
            tag = f"[{entry.tag}]"
            lines.append(
                f"{entry.command:<{command_width}}  {tag:<{tag_width}}  "
                f"{entry.description}")
    lines.extend(("", "[MOTION] commands require explicit operator approval before movement."))
    return "\n".join(lines)


def main() -> int:
    print(render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
