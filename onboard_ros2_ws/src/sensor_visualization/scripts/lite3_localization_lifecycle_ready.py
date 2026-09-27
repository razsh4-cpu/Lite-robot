#!/usr/bin/env python3
"""Deterministically activate and verify the saved-map localization stack.

This process owns no robot transport and publishes no motion commands.  A
non-zero exit asks the outer localization supervisor to tear down the whole
localization launch, wait for DDS cleanup, and retry from a clean state.
"""
from __future__ import annotations

import os
from pathlib import Path
import time


STATE_DIR = Path(os.environ.get("LITE3_STATE_DIR", "/run/lite3-control"))


def atomic_write(name: str, value: str) -> None:
    path = STATE_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def stage(name: str, detail: str = "") -> None:
    atomic_write("LOCALIZATION_STARTUP_STATE", name)
    atomic_write("LOCALIZATION_STARTUP_ERROR", detail)
    print(f"LOCALIZATION_STARTUP_STATE={name} {detail}".rstrip(), flush=True)


def main() -> int:
    import rclpy
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from lifecycle_msgs.msg import State, Transition
    from lifecycle_msgs.srv import ChangeState, GetState
    from nav_msgs.msg import OccupancyGrid
    from rclpy.duration import Duration
    from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
    from tf2_ros import Buffer, TransformException, TransformListener

    rclpy.init(args=None)
    node = rclpy.create_node("lite3_localization_lifecycle_ready")
    tf_buffer = Buffer()
    tf_listener = TransformListener(tf_buffer, node)
    latched = QoSProfile(depth=1)
    latched.reliability = ReliabilityPolicy.RELIABLE
    latched.durability = DurabilityPolicy.TRANSIENT_LOCAL
    seen = {"map": False, "amcl_pose": False}
    node.create_subscription(
        OccupancyGrid, "/map", lambda _msg: seen.__setitem__("map", True), latched)
    node.create_subscription(
        PoseWithCovarianceStamped, "/amcl_pose",
        lambda _msg: seen.__setitem__("amcl_pose", True), latched)

    clients = {}
    for name in ("map_server", "amcl"):
        clients[(name, "get")] = node.create_client(GetState, f"/{name}/get_state")
        clients[(name, "change")] = node.create_client(
            ChangeState, f"/{name}/change_state")

    def call(client, request, timeout=5.0):
        future = client.call_async(request)
        rclpy.spin_until_future_complete(node, future, timeout_sec=timeout)
        return future.result() if future.done() else None

    def wait_services(name: str, timeout=15.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if (clients[(name, "get")].wait_for_service(timeout_sec=0.25)
                    and clients[(name, "change")].wait_for_service(timeout_sec=0.25)):
                return True
        return False

    def get_state(name: str):
        response = call(clients[(name, "get")], GetState.Request())
        return None if response is None else int(response.current_state.id)

    def wait_state(name: str, expected: int, timeout=8.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if get_state(name) == expected:
                return True
            rclpy.spin_once(node, timeout_sec=0.15)
        return False

    def transition(name: str, transition_id: int, expected: int) -> bool:
        for attempt in range(1, 4):
            current = get_state(name)
            if current == expected:
                return True
            request = ChangeState.Request()
            request.transition.id = transition_id
            response = call(clients[(name, "change")], request, timeout=6.0)
            if response is not None and response.success:
                if wait_state(name, expected, timeout=8.0):
                    return True
            print(f"{name} transition {transition_id} attempt {attempt}/3 failed",
                  flush=True)
            time.sleep(1.0)
        return False

    try:
        stage("WAITING_FOR_MAP_SERVER", "waiting for lifecycle services")
        if not wait_services("map_server"):
            stage("STARTUP_FAILED", "map_server lifecycle services unavailable")
            return 21
        if not transition("map_server", Transition.TRANSITION_CONFIGURE,
                          State.PRIMARY_STATE_INACTIVE):
            stage("STARTUP_FAILED", "map_server configure failed after 3 attempts")
            return 22
        if not transition("map_server", Transition.TRANSITION_ACTIVATE,
                          State.PRIMARY_STATE_ACTIVE):
            stage("STARTUP_FAILED", "map_server activate failed after 3 attempts")
            return 23
        map_deadline = time.monotonic() + 10.0
        while time.monotonic() < map_deadline and not seen["map"]:
            rclpy.spin_once(node, timeout_sec=0.2)
        if not seen["map"]:
            stage("STARTUP_FAILED", "map_server active but /map unavailable")
            return 24

        stage("WAITING_FOR_AMCL", "map_server active; activating AMCL")
        if not wait_services("amcl"):
            stage("STARTUP_FAILED", "AMCL lifecycle services unavailable")
            return 31
        if not transition("amcl", Transition.TRANSITION_CONFIGURE,
                          State.PRIMARY_STATE_INACTIVE):
            stage("STARTUP_FAILED", "AMCL configure failed after 3 attempts")
            return 32
        if not transition("amcl", Transition.TRANSITION_ACTIVATE,
                          State.PRIMARY_STATE_ACTIVE):
            stage("STARTUP_FAILED", "AMCL activate failed after 3 attempts")
            return 33

        deadline = time.monotonic() + 25.0
        tf_ready = False
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.2)
            try:
                tf_buffer.lookup_transform(
                    "map", "odom", rclpy.time.Time(),
                    timeout=Duration(seconds=0.05))
                tf_ready = True
            except TransformException:
                pass
            if seen["amcl_pose"] and tf_ready:
                stage("UNLOCALIZED", "localization stack healthy; confidence gate pending")
                return 0
        missing = []
        if not seen["amcl_pose"]:
            missing.append("/amcl_pose")
        if not tf_ready:
            missing.append("map->odom TF")
        stage("STARTUP_FAILED", "AMCL active but missing " + ", ".join(missing))
        return 34
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
