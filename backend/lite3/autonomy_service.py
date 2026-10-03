"""Control only the existing optional AUTONOMY adapter; never write owner files."""
import json
import math
import fcntl
from pathlib import Path
import subprocess
import sys
import time


class SystemdAutonomy:
    UNIT = "lite3-autonomy-command-source.service"

    def __init__(self, state_dir=Path("/run/lite3-control"), motion_approved=False,
                 guard=None, run=subprocess.run):
        self.state_dir = Path(state_dir)
        self.approved = motion_approved is True
        self.guard = Path(guard) if guard else (Path(__file__).resolve().parents[2] /
            "onboard_ros2_ws/src/sensor_visualization/scripts/lite3_posture_guard.py")
        self.run = run
        self.started = False
        self.stop_requested_at = None
        self.reservation = None

    @property
    def pending_cleanup(self):
        return self.started or self.reservation is not None

    def source(self):
        try:
            return (self.state_dir / "COMMAND_SOURCE").read_text().strip() or "UNKNOWN"
        except OSError:
            return "UNKNOWN"

    def _unit(self, operation):
        result = self.run(["sudo", "-n", "systemctl", operation, self.UNIT],
                          text=True, capture_output=True, timeout=8, check=False)
        if result.returncode:
            raise RuntimeError(f"existing AUTONOMY service {operation} failed")

    def acquire(self):
        if not self.approved:
            raise RuntimeError("physical navigation requires explicit approval")
        if self.source() != "NONE":
            raise RuntimeError("command source conflict or unavailable")
        # Serialize backend service requests, not physical command sources.
        # The shared arbiter and its owner.lock remain exclusively authoritative.
        if self.reservation is not None:
            raise RuntimeError("backend cleanup still pending")
        lock = (self.state_dir / "autonomy_backend.lock").open("a")
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock.close()
            raise RuntimeError("another autonomy backend request is active")
        self.reservation = lock
        if self.source() != "NONE":
            self.complete()
            raise RuntimeError("command source changed during acquisition")
        # The established service acquires the arbiter lock, not this backend.
        self.started = True  # retain cleanup obligation on partial start failure
        try:
            self._unit("start")
            deadline = time.monotonic() + 2
            while self.source() == "NONE" and time.monotonic() < deadline:
                time.sleep(0.05)
            if self.source() != "AUTONOMY":
                raise RuntimeError("AUTONOMY acquisition not confirmed")
        except Exception:
            self.release()
            raise

    def release(self):
        if self.started:
            # Existing node shutdown sends zero and ExecStopPost releases safely.
            self.stop_requested_at = time.time()
            self._unit("stop")
            self.started = False

    def stopped(self):
        source = self.source()
        try:
            result = self.run([sys.executable, str(self.guard), "status"],
                              text=True, capture_output=True, timeout=5, check=False)
            status = json.loads(result.stdout) if result.returncode == 0 else {}
            zero = (status.get("high_level_healthy") is True
                    and status.get("telemetry_fresh") is True
                    and status.get("velocities_zero") is True
                    and status.get("motion_enabled") is False)
            # Never confirm this stop using a zero line from before the mission.
            if zero:
                zero = self._current_zero_record()
        except (OSError, ValueError, subprocess.TimeoutExpired):
            zero = False
        return zero, source

    def complete(self):
        """Only called after port proves cancellation, zero and source NONE."""
        if self.reservation is not None:
            fcntl.flock(self.reservation.fileno(), fcntl.LOCK_UN)
            self.reservation.close()
            self.reservation = None

    def _current_zero_record(self):
        if self.stop_requested_at is None:
            return False
        result = self.run(["journalctl", "--no-pager", "-o", "json", "-n", "30",
                           "-u", "lite3-high-level-runtime.service"],
                          text=True, capture_output=True, timeout=3, check=False)
        if result.returncode:
            return False
        now = time.time()
        for line in reversed(result.stdout.splitlines()):
            try:
                record = json.loads(line)
                stamp = float(record["__REALTIME_TIMESTAMP"]) / 1e6
                fields = dict(token.split("=", 1) for token in record["MESSAGE"].split() if "=" in token)
                if "forward" not in fields:
                    continue
                values = [float(fields[name]) for name in ("forward", "lateral", "yaw")]
                return (math.isfinite(stamp) and self.stop_requested_at <= stamp <= now
                        and now - stamp <= 2.5 and fields.get("enabled") == "false"
                        and fields.get("telemetry_fresh") == "true"
                        and fields.get("command_source") == "NONE"
                        and all(math.isfinite(v) and abs(v) <= 1e-6 for v in values))
            except (TypeError, ValueError, KeyError):
                continue
        return False
