#!/usr/bin/env python3
"""Keep robot transport alive; supervise optional Xbox command-source input."""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
import signal
import subprocess
import time


class SystemOps:
    def run(self, args, timeout=None):
        return subprocess.run(
            args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=timeout, check=False).returncode == 0

    def sleep(self, seconds):
        time.sleep(seconds)

    def output(self, args):
        result = subprocess.run(
            args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, check=False)
        return result.stdout if result.returncode == 0 else ""


class XboxReconnectSupervisor:
    def __init__(self, ops=None, env=None):
        self.ops = ops or SystemOps()
        env = env or os.environ
        self.mac = env.get("LITE3_XBOX_MAC", "78:86:2E:B6:8F:C3")
        self.joystick = env.get("LITE3_XBOX_DEVICE", "/dev/input/js0")
        self.attempts = int(env.get("LITE3_XBOX_MAX_ATTEMPTS", "6"))
        self.retry_seconds = float(env.get("LITE3_XBOX_RETRY_SECONDS", "5"))
        self.connect_timeout = float(env.get("LITE3_XBOX_CONNECT_TIMEOUT_SECONDS", "3"))
        self.monitor_seconds = float(env.get("LITE3_XBOX_MONITOR_SECONDS", "1"))
        self.state_dir = Path(env.get("LITE3_STATE_DIR", "/run/lite3-control"))
        self.validator = env.get(
            "LITE3_XBOX_VALIDATOR",
            "/home/abx/ros2_ws/install/sensor_visualization/lib/"
            "sensor_visualization/lite3_xbox_device_valid")
        self.runtime_unit = env.get(
            "LITE3_XBOX_RUNTIME_UNIT", "lite3-high-level-xbox.service")
        self.robot_runtime_unit = env.get(
            "LITE3_ROBOT_RUNTIME_UNIT", "lite3-high-level-runtime.service")
        self.supervise = env.get("LITE3_XBOX_SUPERVISE", "true").lower() == "true"
        self.stop_requested = False
        self.started_runtime = False

    def log(self, message):
        print(f"lite3-xbox-supervisor: {message}", flush=True)

    def write_state(self, name, value):
        self.state_dir.mkdir(parents=True, exist_ok=True)
        (self.state_dir / name).write_text(f"{value}\n", encoding="utf-8")

    def validate(self):
        info = self.ops.output(["bluetoothctl", "info", self.mac])
        return ("Connected: yes" in info
                and self.ops.run([self.validator, self.joystick]))

    def connect(self):
        try:
            return self.ops.run(
                ["bluetoothctl", "connect", self.mac], timeout=self.connect_timeout)
        except subprocess.TimeoutExpired:
            return False

    def runtime_active(self):
        return self.ops.run(
            ["systemctl", "is-active", "--quiet", self.runtime_unit])

    def robot_runtime_active(self):
        return self.ops.run(
            ["systemctl", "is-active", "--quiet", self.robot_runtime_unit])

    def ensure_robot_runtime(self):
        if self.robot_runtime_active():
            return True
        if not self.ops.run(["systemctl", "start", self.robot_runtime_unit]):
            self.log("persistent robot high-level runtime failed to start")
            return False
        self.log("persistent robot high-level runtime started independently of Xbox")
        return True

    def lease_available(self):
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with (self.state_dir / "owner.lock").open("a+") as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return False
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            return True

    def start_runtime(self):
        if self.runtime_active():
            self.log("LOCAL_XBOX input runtime already active; not duplicating it")
            return True
        if not self.lease_available():
            self.log("command-source lease is owned; LOCAL_XBOX will not take over")
            return False
        if not self.ops.run(["systemctl", "start", self.runtime_unit]):
            self.log("LOCAL_XBOX input runtime failed to start")
            return False
        self.started_runtime = True
        self.log("LOCAL_XBOX input started fresh; robot runtime was not restarted")
        return True

    def mark_unavailable(self):
        self.write_state("MANUAL_CONTROL_AVAILABLE", "false")
        if self.lease_available():
            self.write_state("COMMAND_SOURCE", "NONE")

    def initial_window(self):
        for attempt in range(1, self.attempts + 1):
            if self.validate():
                self.write_state("MANUAL_CONTROL_AVAILABLE", "true")
                self.log(f"Xbox verified on {self.joystick} ({attempt}/{self.attempts})")
                return True
            self.log(f"Xbox unavailable; connection attempt {attempt}/{self.attempts}")
            self.connect()
            if attempt < self.attempts:
                self.ops.sleep(self.retry_seconds)
        self.mark_unavailable()
        self.log("Xbox unavailable after finite startup window; system continues normally")
        return False

    def reconnect_until_ready(self):
        attempt = 0
        while not self.stop_requested:
            attempt += 1
            if self.validate():
                self.write_state("MANUAL_CONTROL_AVAILABLE", "true")
                if self.start_runtime():
                    self.log(f"Xbox recovered after reconnect attempt {attempt}")
                    return True
                self.ops.sleep(self.retry_seconds)
                continue
            self.mark_unavailable()
            self.log(f"Xbox disconnected/unavailable; reconnect attempt {attempt}")
            self.connect()
            self.ops.sleep(self.retry_seconds)
        return False

    def supervise_runtime(self):
        while not self.stop_requested:
            while self.runtime_active() and not self.stop_requested:
                self.ops.sleep(self.monitor_seconds)
            if self.stop_requested:
                break
            self.mark_unavailable()
            self.log("Xbox input stopped after disconnect; robot runtime and odometry retained")
            if not self.reconnect_until_ready():
                break

    def shutdown(self, *_args):
        self.stop_requested = True
        if self.started_runtime or self.runtime_active():
            self.ops.run(["systemctl", "stop", self.runtime_unit])
        self.mark_unavailable()
        self.log("supervisor stopped; LOCAL_XBOX unavailable")

    def run(self):
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.write_state("MANUAL_CONTROL_AVAILABLE", "false")
        if not (self.state_dir / "COMMAND_SOURCE").exists():
            self.write_state("COMMAND_SOURCE", "NONE")
        if not (self.state_dir / "AUTONOMY_READY").exists():
            self.write_state("AUTONOMY_READY", "false")
        if not self.ensure_robot_runtime():
            return 1
        if not self.initial_window():
            return 0
        if not self.start_runtime():
            return 0
        if self.supervise:
            self.supervise_runtime()
        return 0


def main():
    supervisor = XboxReconnectSupervisor()
    signal.signal(signal.SIGINT, supervisor.shutdown)
    signal.signal(signal.SIGTERM, supervisor.shutdown)
    raise SystemExit(supervisor.run())


if __name__ == "__main__":
    main()
