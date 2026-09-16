#!/usr/bin/env python3
"""Planning-only bridge: RViz goal_pose -> Nav2 path, never cmd_vel."""

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import ComputePathToPose
from nav_msgs.msg import Path


class PlanFromRvizGoal(Node):
    def __init__(self):
        super().__init__('plan_from_rviz_goal')
        self.path_pub = self.create_publisher(Path, '/planned_path', 10)
        self.goal_sub = self.create_subscription(PoseStamped, '/goal_pose', self.on_goal, 10)
        self.client = ActionClient(self, ComputePathToPose, '/compute_path_to_pose')
        self.get_logger().info('Planning-only bridge ready: select a 2D Goal Pose in RViz.')

    def on_goal(self, pose):
        if not self.client.wait_for_server(timeout_sec=1.0):
            self.get_logger().warning('Planner server is not ready yet.')
            return
        request = ComputePathToPose.Goal()
        request.goal = pose
        request.use_start = False
        request.planner_id = 'GridBased'
        self.client.send_goal_async(request).add_done_callback(self.goal_response)

    def goal_response(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().warning('Planner rejected the selected goal.')
            return
        handle.get_result_async().add_done_callback(self.path_result)

    def path_result(self, future):
        result = future.result().result
        if result.error_code != ComputePathToPose.Result.NONE:
            self.get_logger().warning(f'No path: {result.error_msg} (code {result.error_code})')
            return
        self.path_pub.publish(result.path)
        self.get_logger().info(f'Published plan with {len(result.path.poses)} poses. No motion command was sent.')


def main():
    rclpy.init()
    node = PlanFromRvizGoal()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
