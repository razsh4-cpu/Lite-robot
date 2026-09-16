#!/usr/bin/env python3
"""Read-only, one-shot manual-motion validator for LiDAR odometry.

It saves each received odometry sample and checks RTAB-Map's OdomInfo quality
stream. It never publishes commands or transforms.
"""

import csv
import math
from pathlib import Path
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rtabmap_msgs.msg import OdomInfo
from std_msgs.msg import Bool, Float32


def yaw_from_quaternion(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def angle_delta(a, b):
    return math.atan2(math.sin(a - b), math.cos(a - b))


class MotionMonitor(Node):
    def __init__(self):
        super().__init__('lidar_odom_motion_monitor')
        self.sub = self.create_subscription(Odometry, '/odom', self.on_odom, 20)
        self.info_sub = self.create_subscription(OdomInfo, '/odom_info', self.on_info, 20)
        self.cmd_sub = self.create_subscription(Twist, '/cmd_vel', self.on_cmd, 20)
        self.forward_sub = self.create_subscription(
            Float32, '/lite3/manual_forward_normalized', self.on_forward, 20)
        self.yaw_sub = self.create_subscription(
            Float32, '/lite3/manual_yaw_normalized', self.on_yaw, 20)
        self.deadman_sub = self.create_subscription(
            Bool, '/lite3/manual_axis_deadman', self.on_deadman, 20)
        self.timer = self.create_timer(0.1, self.step)
        self.csv_path = Path('/tmp') / ('lite3_icp_slow_test_%d.csv' % time.time_ns())
        self.csv_file = self.csv_path.open('w', newline='')
        self.csv = csv.writer(self.csv_file)
        self.csv.writerow(['stamp_s', 'x_m', 'y_m', 'yaw_rad', 'linear_m_s',
                           'angular_rad_s', 'lost', 'icp_inliers_ratio',
                           'icp_translation_m', 'icp_rotation_rad',
                           'cmd_linear_x', 'cmd_angular_z',
                           'normalized_forward', 'normalized_yaw', 'deadman'])
        self.latest = None
        self.latest_info = None
        self.state = 'WAITING_FOR_ODOM'
        self.start = None
        self.last = None
        self.motion_started = None
        self.stopped_since = None
        self.path_length = 0.0
        self.peak_linear = 0.0
        self.peak_angular = 0.0
        self.min_ratio = float('inf')
        self.lost_count = 0
        self.pose_jump_count = 0
        self.max_step = 0.0
        self.max_yaw_step = 0.0
        self.last_rx_time = None
        self.cmd_linear_x = 0.0
        self.cmd_angular_z = 0.0
        self.normalized_forward = 0.0
        self.normalized_yaw = 0.0
        self.deadman = False

    def on_cmd(self, msg):
        self.cmd_linear_x = float(msg.linear.x)
        self.cmd_angular_z = float(msg.angular.z)

    def on_forward(self, msg):
        self.normalized_forward = float(msg.data)

    def on_yaw(self, msg):
        self.normalized_yaw = float(msg.data)

    def on_deadman(self, msg):
        self.deadman = bool(msg.data)

    def pose(self, msg):
        p = msg.pose.pose.position
        return (p.x, p.y, yaw_from_quaternion(msg.pose.pose.orientation),
                msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9)

    def on_odom(self, msg):
        self.latest = msg
        self.last_rx_time = self.get_clock().now().nanoseconds * 1e-9
        linear = math.hypot(msg.twist.twist.linear.x, msg.twist.twist.linear.y)
        angular = abs(msg.twist.twist.angular.z)
        pose = self.pose(msg)
        if self.state == 'MOVING':
            self.peak_linear = max(self.peak_linear, linear)
            self.peak_angular = max(self.peak_angular, angular)
            if self.last is not None:
                step = math.hypot(pose[0] - self.last[0], pose[1] - self.last[1])
                yaw_step = abs(angle_delta(pose[2], self.last[2]))
                self.path_length += step
                self.max_step = max(self.max_step, step)
                self.max_yaw_step = max(self.max_yaw_step, yaw_step)
                if step > 0.06 or yaw_step > 0.15:
                    self.pose_jump_count += 1
            self.csv.writerow([pose[3], pose[0], pose[1], pose[2], linear, angular,
                               self.latest_info.lost if self.latest_info else '',
                               self.latest_info.icp_inliers_ratio if self.latest_info else '',
                               self.latest_info.icp_translation if self.latest_info else '',
                               self.latest_info.icp_rotation if self.latest_info else '',
                               self.cmd_linear_x, self.cmd_angular_z,
                               self.normalized_forward, self.normalized_yaw,
                               int(self.deadman)])
            self.csv_file.flush()
        self.last = pose

    def on_info(self, msg):
        self.latest_info = msg
        if self.state == 'MOVING':
            self.min_ratio = min(self.min_ratio, msg.icp_inliers_ratio)
            if msg.lost:
                self.lost_count += 1

    def step(self):
        if self.latest is None:
            return
        now = self.get_clock().now().nanoseconds * 1e-9
        if self.state == 'WAITING_FOR_ODOM':
            self.start = self.pose(self.latest)
            self.state = 'ARMED'
            self.get_logger().info(
                'READY: start x=%.4f m y=%.4f m yaw=%.3f deg. Move manually, then stop.' %
                (self.start[0], self.start[1], math.degrees(self.start[2])))
            return

        linear = math.hypot(self.latest.twist.twist.linear.x,
                            self.latest.twist.twist.linear.y)
        angular = abs(self.latest.twist.twist.angular.z)
        moving = linear > 0.05 or angular > 0.08
        if self.state == 'ARMED' and moving:
            self.state = 'MOVING'
            self.motion_started = now
            self.last = self.start
            self.path_length = 0.0
            self.peak_linear = 0.0
            self.peak_angular = 0.0
            self.get_logger().info('Motion detected; recording trajectory.')
            return
        if self.state != 'MOVING':
            return
        if moving:
            self.stopped_since = None
        elif self.stopped_since is None:
            self.stopped_since = now
        elif now - self.stopped_since >= 2.0:
            end = self.pose(self.latest)
            dx, dy = end[0] - self.start[0], end[1] - self.start[1]
            displacement = math.hypot(dx, dy)
            yaw = angle_delta(end[2], self.start[2])
            duration = now - self.motion_started
            ratio = 'n/a' if math.isinf(self.min_ratio) else '%.3f' % self.min_ratio
            self.get_logger().info(
                'RESULT displacement=%.4f m dx=%.4f m dy=%.4f m yaw=%.3f deg '
                'path=%.4f m duration=%.2f s peak_linear=%.3f m/s peak_angular=%.3f rad/s '
                'min_correspondence=%s lost_messages=%d pose_jumps=%d '
                'max_step=%.4f m max_yaw_step=%.3f deg csv=%s' %
                (displacement, dx, dy, math.degrees(yaw), self.path_length,
                 duration, self.peak_linear, self.peak_angular, ratio,
                 self.lost_count, self.pose_jump_count, self.max_step,
                 math.degrees(self.max_yaw_step), self.csv_path))
            self.csv_file.close()
            rclpy.shutdown()


def main():
    rclpy.init()
    node = MotionMonitor()
    try:
        rclpy.spin(node)
    finally:
        if not node.csv_file.closed:
            node.csv_file.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
