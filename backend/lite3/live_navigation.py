"""Independent Nav2 action binding; never publishes velocity or vendor commands."""
from __future__ import annotations

import time
from .autonomy import StopConfirmation


class LiveNavigationPort:
    """One tracked Nav2 request and one existing AUTONOMY service ownership.

    Unknown acceptance/cancel outcomes remain tracked until terminal confirmation.
    Release suppresses physical output even when Nav2 cancellation is uncertain.
    """
    def __init__(self, transport, authority, timeout=5.0):
        self.transport, self.authority = transport, authority
        self.timeout = timeout
        self.request_id = None
        self.goal = None
        self.future = None
        self.handle = None
        self.owned = False
        self.state = "IDLE"
        self.no_goal_known = True

    def start(self, request_id, goal):
        if self.request_id is not None:
            raise RuntimeError("previous navigation/stop unconfirmed")
        # No goal submission without explicit approval and exclusive ownership.
        try:
            self.authority.acquire()
        except Exception:
            if getattr(self.authority, "pending_cleanup", getattr(self.authority, "started", False)):
                self.owned = True
                self.request_id, self.goal = request_id, goal
                self.state = "ACQUIRE_FAILED"
            raise
        self.owned = True
        self.request_id, self.goal = request_id, goal
        self.state = "SUBMITTING"
        try:
            self.no_goal_known = False
            self.future = self.transport.send(goal)
            self.handle = self.transport.accepted_handle(self.future, self.timeout)
            if self.handle is None:
                self.no_goal_known = True
                self.state = "REJECTED"
                raise RuntimeError("Nav2 goal rejected")
            self.state = "RUNNING"
        except Exception:
            # Caller can retry stop; do not forget a potentially accepted goal.
            self.state = "STOPPING" if self.state != "REJECTED" else self.state
            raise

    def poll(self):
        if self.handle is None:
            return None
        result = self.transport.result(self.handle)
        if result is None:
            return None
        self.state = result
        return self.request_id, result

    def stop(self, request_id):
        if self.request_id is not None and request_id != self.request_id:
            return StopConfirmation(False, False, False, "UNKNOWN")
        cancelled = self.no_goal_known
        self.state = "STOPPING"
        # Suppress the existing physical adapter FIRST. Waiting for a stalled
        # action server must not prolong navigation's fresh velocity stream.
        if self.owned:
            self.authority.release()
            self.owned = False
        try:
            if self.future is not None and self.handle is None and not cancelled:
                self.handle = self.transport.accepted_handle(self.future, self.timeout)
                cancelled = self.handle is None
            if self.handle is not None:
                cancelled = self.transport.result(self.handle) is not None
                if not cancelled:
                    cancelled = self.transport.cancel(self.handle, self.timeout)
        except Exception:
            cancelled = False
        zero, source = self.authority.stopped()
        confirmation = StopConfirmation(cancelled, zero, source == "NONE", source)
        if confirmation.safe:
            if hasattr(self.authority, "complete"):
                self.authority.complete()
            if self.handle is not None and hasattr(self.transport, "forget"):
                self.transport.forget(self.handle)
            self.request_id = self.future = self.handle = None
            self.no_goal_known = True
            self.state = "IDLE"
        return confirmation

    def status(self):
        return {"request_id": self.request_id, "goal": self.goal,
                "state": self.state, "observed_monotonic": time.monotonic()}


class RosNav2Transport:
    """Concrete ROS2 transport. Construction requires an already running ROS node.

    Imports are lazy so offline tests need no ROS installation. The caller owns
    spinning and lifecycle; no background node/service is implicitly started.
    """
    def __init__(self, node):
        import rclpy
        from rclpy.action import ActionClient
        from nav2_msgs.action import NavigateToPose
        self.node, self.rclpy, self.action = node, rclpy, NavigateToPose
        self.client = ActionClient(node, NavigateToPose, "/navigate_to_pose")
        self.results = {}
        self.distance_remaining = None

    def _wait(self, future, timeout):
        self.rclpy.spin_until_future_complete(self.node, future, timeout_sec=timeout)
        if not future.done():
            raise TimeoutError("Nav2 response timeout")
        return future.result()

    def send(self, pose):
        import math
        if pose.get("frame_id") != "map":
            raise ValueError("navigation goal must use map frame")
        values = [pose[group][key] for group, keys in
                  (("position", ("x", "y", "z")),
                   ("orientation", ("x", "y", "z", "w"))) for key in keys]
        if not all(math.isfinite(v) for v in values):
            raise ValueError("nonfinite navigation goal")
        if not self.client.wait_for_server(timeout_sec=3.0):
            raise RuntimeError("NavigateToPose unavailable")
        goal = self.action.Goal()
        goal.pose.header.frame_id = "map"
        goal.pose.header.stamp = self.node.get_clock().now().to_msg()
        for key, value in pose["position"].items():
            setattr(goal.pose.pose.position, key, value)
        for key, value in pose["orientation"].items():
            setattr(goal.pose.pose.orientation, key, value)
        return self.client.send_goal_async(goal, feedback_callback=self._feedback)

    def _feedback(self, message):
        self.distance_remaining = message.feedback.distance_remaining

    def accepted_handle(self, future, timeout):
        handle = self._wait(future, timeout)
        if handle is None or not handle.accepted:
            return None
        if id(handle) not in self.results:
            self.results[id(handle)] = handle.get_result_async()
        return handle

    def result(self, handle):
        future = self.results[id(handle)]
        if not future.done():
            return None
        wrapped = future.result()
        if wrapped is None:
            return None
        if wrapped.status not in (4, 5, 6):
            return None
        # ROS action terminal statuses: succeeded=4, canceled=5, aborted=6.
        code = getattr(wrapped.result, "error_code", None)
        if wrapped.status == 4 and code == 0:
            return "SUCCEEDED"
        return "CANCELLED" if wrapped.status == 5 else "FAILED"

    def forget(self, handle):
        self.results.pop(id(handle), None)

    def cancel(self, handle, timeout):
        response = self._wait(handle.cancel_goal_async(), timeout)
        if response is None or response.return_code != 0:
            return self.result(handle) is not None
        # A cancel acknowledgement alone does not prove the controller stopped.
        try:
            self._wait(self.results[id(handle)], timeout)
        except TimeoutError:
            return False
        return self.result(handle) is not None
