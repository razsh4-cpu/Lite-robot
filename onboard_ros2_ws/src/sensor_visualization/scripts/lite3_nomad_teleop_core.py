#!/usr/bin/env python3
"""Pure Phase-3C TeleopIntent/v2 safety state machine (no I/O)."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
import time


FIELDS = {
    "schema", "schema_version", "robot_id", "intent_id", "session_id",
    "operator_lease_id", "lease_generation", "authority_id", "control_epoch",
    "sequence", "action", "vx", "vy", "wz", "deadman_active", "issued_at",
    "expires_at", "execution_mode",
}
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")


@dataclass(frozen=True)
class TeleopConfig:
    max_vx: float = 0.10
    max_vy: float = 0.05
    max_wz: float = 0.20
    intent_ttl_s: float = 0.25
    watchdog_s: float = 0.30
    stand_timeout_s: float = 20.0
    status_stale_s: float = 1.0
    minimum_battery_percent: float = 25.0


@dataclass(frozen=True)
class JoyFrame:
    axes: list
    buttons: list


@dataclass(frozen=True)
class Decision:
    status: dict
    joy: JoyFrame
    acquire: bool = False
    release: bool = False


def neutral_joy():
    return JoyFrame([0.0] * 8, [0] * 15)


def stand_joy():
    buttons = [0] * 15
    buttons[0] = 1  # Existing Xbox bridge mapping: A -> SIT_STAND edge.
    return JoyFrame([0.0] * 8, buttons)


def _shape_axis(value, deadzone=0.05):
    value = max(-1.0, min(1.0, float(value)))
    if abs(value) <= deadzone:
        return 0.0
    return math.copysign(min(1.0, (abs(value) - deadzone) / (1.0 - deadzone)), value)


def _inverse_shape(value, deadzone=0.05):
    value = max(-1.0, min(1.0, float(value)))
    if value == 0.0:
        return 0.0
    return math.copysign(deadzone + (1.0 - deadzone) * abs(value), value)


def velocity_to_joy(vx, vy, wz, deadman):
    axes = [0.0] * 8
    axes[0] = _inverse_shape(-vy)
    axes[1] = _inverse_shape(vx)
    axes[2] = _inverse_shape(wz)
    buttons = [0] * 15
    buttons[10] = 1 if deadman else 0
    return JoyFrame(axes, buttons)


def joy_to_velocity(joy):
    return tuple(round(value, 9) for value in (
        _shape_axis(joy.axes[1]), -_shape_axis(joy.axes[0]),
        _shape_axis(joy.axes[2])))


class PhysicalTeleopMachine:
    """Validate v2 and return an inert or eligible protected-Joy decision."""

    def __init__(self, robot_id, config=None, clock=None,
                 physical_output_enabled=False):
        if not isinstance(robot_id, str) or not IDENTIFIER.fullmatch(robot_id):
            raise ValueError("invalid robot_id")
        self.robot_id = robot_id
        self.config = config or TeleopConfig()
        self.clock = clock or time.time
        self.physical_output_enabled = bool(physical_output_enabled)
        self.state = "WAITING_FOR_CONTEXT"
        self.reason = "INITIAL_STATE"
        self.result = "ZEROED"
        self.identity = None
        self.last_sequence = None
        self.last_intent_id = None
        self.last_accepted_at = None
        self.stand_requested_at = None
        self.lease_requested = False
        self.velocity = (0.0, 0.0, 0.0)

    @staticmethod
    def _finite(value):
        return (not isinstance(value, bool) and isinstance(value, (int, float))
                and math.isfinite(float(value)))

    def _status(self):
        now = float(self.clock())
        identity = self.identity or {}
        return {
            "schema": "robot.teleop_status", "schema_version": 2,
            "robot_id": self.robot_id, "state": self.state,
            "result": self.result, "reason": self.reason,
            "session_id": identity.get("session_id"),
            "operator_lease_id": identity.get("operator_lease_id"),
            "lease_generation": identity.get("lease_generation"),
            "authority_id": identity.get("authority_id"),
            "control_epoch": identity.get("control_epoch", 0),
            "last_sequence": self.last_sequence,
            "last_intent_id": self.last_intent_id,
            "vx": self.velocity[0], "vy": self.velocity[1],
            "wz": self.velocity[2],
            "deadman_active": self.state == "ACTIVE",
            "watchdog_state": "ACTIVE" if self.state == "ACTIVE" else (
                "STOPPED" if self.state == "WATCHDOG_STOPPED" else "IDLE"),
            "observed_at": self.last_accepted_at, "published_at": now,
            "execution_mode": "PHYSICAL_MANUAL",
            "physical_output_enabled": self.physical_output_enabled,
            "motion_commands_supported": self.physical_output_enabled,
            "physical_output_performed": False,
        }

    def status(self):
        return self._status()

    def _stop(self, state, reason, result="REJECTED"):
        release = self.lease_requested
        self.lease_requested = False
        self.velocity = (0.0, 0.0, 0.0)
        self.state, self.reason, self.result = state, reason, result
        return Decision(self._status(), neutral_joy(), release=release)

    def _request_failure(self, request):
        if not isinstance(request, dict) or set(request) != FIELDS:
            return "MALFORMED_REQUEST"
        if request.get("schema") != "robot.teleop_intent" or request.get("schema_version") != 2:
            return "UNSUPPORTED_SCHEMA"
        if request.get("execution_mode") != "PHYSICAL_MANUAL":
            return "UNSUPPORTED_EXECUTION_MODE"
        if request.get("robot_id") != self.robot_id:
            return "WRONG_ROBOT"
        for field in ("intent_id", "session_id", "operator_lease_id", "authority_id"):
            if not isinstance(request.get(field), str) or not IDENTIFIER.fullmatch(request[field]):
                return "MALFORMED_REQUEST"
        for field in ("lease_generation", "control_epoch", "sequence"):
            if type(request.get(field)) is not int or request[field] < 0:
                return "MALFORMED_REQUEST"
        if request.get("action") not in {"DRIVE", "ZERO", "STAND"}:
            return "MALFORMED_REQUEST"
        if type(request.get("deadman_active")) is not bool:
            return "MALFORMED_REQUEST"
        for field in ("vx", "vy", "wz", "issued_at", "expires_at"):
            if not self._finite(request.get(field)):
                return "MALFORMED_REQUEST"
        now = float(self.clock())
        if float(request["expires_at"]) <= now:
            return "REQUEST_EXPIRED"
        if (float(request["issued_at"]) > now + 1.0
                or float(request["expires_at"]) - float(request["issued_at"])
                > self.config.intent_ttl_s + 1e-9):
            return "MALFORMED_REQUEST"
        if (abs(float(request["vx"])) > self.config.max_vx
                or abs(float(request["vy"])) > self.config.max_vy
                or abs(float(request["wz"])) > self.config.max_wz):
            return "VELOCITY_OUT_OF_RANGE"
        if request["action"] in {"ZERO", "STAND"}:
            if request["deadman_active"] or any(float(request[key]) != 0.0 for key in ("vx", "vy", "wz")):
                return "MALFORMED_REQUEST"
        elif not request["deadman_active"]:
            return "DEADMAN_REQUIRED"
        return None

    def _context_failure(self, platform, authority, require_standing=True):
        now = float(self.clock())
        if not isinstance(platform, dict) or platform.get("schema") != "robot.platform_status":
            return "PLATFORM_STATUS_INVALID"
        if platform.get("schema_version") != 1 or platform.get("robot_id") != self.robot_id:
            return "PLATFORM_STATUS_INVALID"
        observed = platform.get("observed_at")
        if not self._finite(observed) or not 0 <= now - float(observed) <= self.config.status_stale_s:
            return "PLATFORM_STATUS_STALE"
        connectivity = platform.get("connectivity") or {}
        robot = platform.get("robot_state") or {}
        safety = platform.get("safety") or {}
        if connectivity.get("online") is not True:
            return "ROBOT_OFFLINE"
        if robot.get("high_level_health") != "READY":
            return "HIGH_LEVEL_UNHEALTHY"
        if require_standing and robot.get("posture") != "STANDING":
            return "POSTURE_NOT_STANDING"
        battery = robot.get("battery_percent")
        if not self._finite(battery) or float(battery) < self.config.minimum_battery_percent:
            return "BATTERY_NOT_READY"
        if safety.get("watchdog_state") != "OK":
            return "PLATFORM_WATCHDOG_NOT_READY"
        source = safety.get("command_source")
        owner = safety.get("robot_side_owner")
        if source not in {"NONE", "LAPTOP_XBOX"}:
            return "COMMAND_SOURCE_CONFLICT"
        if not isinstance(authority, dict) or authority.get("schema") != "robot.control_authority":
            return "AUTHORITY_INVALID"
        if authority.get("schema_version") != 1 or authority.get("robot_id") != self.robot_id:
            return "AUTHORITY_INVALID"
        if authority.get("state") != "RESERVED":
            return "AUTHORITY_NOT_RESERVED"
        published, expires = authority.get("published_at"), authority.get("expires_at")
        if (not self._finite(published) or not self._finite(expires)
                or not 0 <= now - float(published) <= self.config.status_stale_s
                or float(expires) <= now):
            return "AUTHORITY_STALE"
        if source == "LAPTOP_XBOX" and owner != authority.get("authority_id"):
            return "ROBOT_SIDE_OWNER_MISMATCH"
        return None

    @staticmethod
    def _request_identity(request):
        return {field: request[field] for field in (
            "session_id", "operator_lease_id", "lease_generation",
            "authority_id", "control_epoch")}

    def handle(self, request, platform, authority):
        failure = self._request_failure(request)
        if failure:
            return self._stop("BLOCKED", failure)
        stand_action = request["action"] == "STAND"
        failure = self._context_failure(
            platform, authority, require_standing=request["action"] == "DRIVE")
        if failure:
            return self._stop("BLOCKED", failure)
        identity = self._request_identity(request)
        if any(identity.get(key) != authority.get(key) for key in identity):
            return self._stop("BLOCKED", "AUTHORITY_MISMATCH")
        if self.identity is not None and identity != self.identity:
            self.identity = identity
            self.last_sequence = None
            self.state = "WAITING_FOR_NEUTRAL"
            return self._stop("WAITING_FOR_NEUTRAL", "CONTROL_EPOCH_CHANGED")
        self.identity = identity
        if self.last_sequence is not None and request["sequence"] <= self.last_sequence:
            return self._stop("BLOCKED", "SEQUENCE_REPLAY")
        self.last_sequence = request["sequence"]
        self.last_intent_id = request["intent_id"]
        self.last_accepted_at = float(self.clock())
        if request["action"] == "STAND":
            if (platform.get("robot_state") or {}).get("posture") == "STANDING":
                self.stand_requested_at = None
                self.velocity = (0.0, 0.0, 0.0)
                self.state, self.result, self.reason = (
                    "WAITING_FOR_NEUTRAL", "ZEROED", "ALREADY_STANDING")
                return Decision(self._status(), neutral_joy())
            if self.state not in {"ARMED", "OUTPUT_DISABLED"}:
                return self._stop("WAITING_FOR_NEUTRAL", "NEUTRAL_REQUIRED")
            if not self.physical_output_enabled:
                self.velocity = (0.0, 0.0, 0.0)
                self.state, self.result, self.reason = (
                    "OUTPUT_DISABLED", "ZEROED", "PHYSICAL_OUTPUT_DISABLED")
                return Decision(self._status(), neutral_joy())
            self.lease_requested = True
            self.stand_requested_at = float(self.clock())
            self.velocity = (0.0, 0.0, 0.0)
            self.state, self.result, self.reason = (
                "WAITING_FOR_STANDING", "ACCEPTED", "STAND_REQUESTED")
            return Decision(self._status(), stand_joy(), acquire=True)
        if request["action"] == "ZERO":
            if self.state == "WAITING_FOR_STANDING":
                self.reason = "STAND_IN_PROGRESS"
                return Decision(self._status(), neutral_joy())
            release = self.lease_requested
            self.lease_requested = False
            self.velocity = (0.0, 0.0, 0.0)
            self.state, self.result, self.reason = "ARMED", "ZEROED", None
            return Decision(self._status(), neutral_joy(), release=release)
        if self.state not in {"ARMED", "ACTIVE", "OUTPUT_DISABLED"}:
            return self._stop("WAITING_FOR_NEUTRAL", "NEUTRAL_REQUIRED")
        self.lease_requested = True
        if not self.physical_output_enabled:
            self.velocity = (0.0, 0.0, 0.0)
            self.state, self.result, self.reason = (
                "OUTPUT_DISABLED", "ZEROED", "PHYSICAL_OUTPUT_DISABLED")
            return Decision(self._status(), neutral_joy(), acquire=True)
        self.velocity = tuple(float(request[key]) for key in ("vx", "vy", "wz"))
        self.state, self.result, self.reason = "ACTIVE", "ACCEPTED", None
        return Decision(self._status(), velocity_to_joy(*self.velocity, True), acquire=True)

    def tick(self, platform, authority):
        waiting_for_stand = self.state == "WAITING_FOR_STANDING"
        failure = self._context_failure(
            platform, authority, require_standing=self.state == "ACTIVE")
        if failure:
            return self._stop("BLOCKED", failure)
        if waiting_for_stand:
            now = float(self.clock())
            if (platform.get("robot_state") or {}).get("posture") == "STANDING":
                self.stand_requested_at = None
                self.state, self.result, self.reason = (
                    "WAITING_FOR_NEUTRAL", "ZEROED", "STANDING_CONFIRMED")
                return Decision(self._status(), neutral_joy())
            if (self.stand_requested_at is None
                    or now - self.stand_requested_at > self.config.stand_timeout_s):
                self.stand_requested_at = None
                return self._stop("BLOCKED", "STAND_CONFIRMATION_TIMEOUT")
            return Decision(self._status(), neutral_joy())
        if self.identity is not None:
            authority_identity = {field: authority.get(field) for field in self.identity}
            if authority_identity != self.identity:
                self.identity = authority_identity
                self.last_sequence = None
                return self._stop("WAITING_FOR_NEUTRAL", "CONTROL_EPOCH_CHANGED")
        now = float(self.clock())
        if self.last_accepted_at is not None and now - self.last_accepted_at > self.config.watchdog_s:
            self.last_sequence = None
            return self._stop("WATCHDOG_STOPPED", "INTENT_WATCHDOG_EXPIRED",
                              "WATCHDOG_STOPPED")
        return Decision(self._status(), neutral_joy())
