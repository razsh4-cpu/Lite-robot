"""Read-only guard for staging navigation against the existing INERT runtime."""
import json
from pathlib import Path
import subprocess


def validate_boundary(source, autonomy_active, sable_active, receiver_count,
                      high_level_count, params):
    if source != "NONE" or autonomy_active:
        raise ValueError("physical AUTONOMY/ownership must remain inactive")
    if sable_active:
        raise ValueError("SABLE must be stopped before independent validation")
    if receiver_count != 1 or high_level_count != 1:
        raise ValueError("exactly one existing HIGH-LEVEL/UDP receiver required")
    if (params.get("transmit") is not False or params.get("zero_only") is not True
            or params.get("require_deadman") is not True):
        raise ValueError("existing runtime is not confirmed INERT/deadman-protected")


def active(name):
    return subprocess.run(["systemctl", "is-active", "--quiet", name],
                          timeout=3, check=False).returncode == 0


def inspect():
    import rclpy
    from rcl_interfaces.srv import GetParameters
    rclpy.init()
    node = rclpy.create_node("lite3_autonomy_validation_boundary")
    try:
        for _ in range(15):
            rclpy.spin_once(node, timeout_sec=0.2)
        client = node.create_client(GetParameters, "/lite3_high_level_runtime/get_parameters")
        if not client.wait_for_service(timeout_sec=3):
            raise ValueError("existing HIGH-LEVEL parameter service unavailable")
        request = GetParameters.Request()
        request.names = ["transmit", "zero_only", "require_deadman"]
        future = client.call_async(request)
        rclpy.spin_until_future_complete(node, future, timeout_sec=3)
        response = future.result() if future.done() else None
        params = {k: v.bool_value for k, v in zip(request.names, response.values)
                  if v.type == 1} if response else {}
        receiver = subprocess.run(["ss", "-H", "-uln", "sport = :43897"],
                                  capture_output=True, text=True, timeout=3, check=True)
        state = dict(source=Path("/run/lite3-control/COMMAND_SOURCE").read_text().strip(),
                     autonomy_active=active("lite3-autonomy-command-source.service"),
                     sable_active=any(active(n) for n in ("sable-edge.service", "sable-ros.service")),
                     receiver_count=len(receiver.stdout.splitlines()),
                     high_level_count=node.get_node_names().count("lite3_high_level_runtime"),
                     params=params)
        validate_boundary(**state)
        competing = set(node.get_node_names()) & {"map_server", "amcl", "controller_server",
            "planner_server", "bt_navigator", "sllidar_node", "base_to_lidar_tf"}
        if competing:
            raise ValueError("navigation/sensor nodes already running: " + ", ".join(sorted(competing)))
        print(json.dumps(state, sort_keys=True))
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    inspect()
