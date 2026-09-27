#!/usr/bin/env python3
"""Passive D455 aligned-depth centre-pixel probe for sensor bring-up."""

import statistics

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class CenterDepthProbe(Node):
    def __init__(self):
        super().__init__('d455_center_depth_probe')
        self.subscription = self.create_subscription(
            Image,
            '/camera/camera/aligned_depth_to_color/image_raw',
            self.image_callback,
            10,
        )
        self.last_log_ns = 0

    def image_callback(self, msg: Image) -> None:
        now_ns = self.get_clock().now().nanoseconds
        if now_ns - self.last_log_ns < 500_000_000:
            return
        self.last_log_ns = now_ns
        if msg.width < 5 or msg.height < 5 or msg.encoding not in ('16UC1', '32FC1'):
            self.get_logger().warning(
                f'Unsupported aligned-depth image: {msg.width}x{msg.height} {msg.encoding}'
            )
            return

        bytes_per_pixel = 2 if msg.encoding == '16UC1' else 4
        values = []
        center_x, center_y = msg.width // 2, msg.height // 2
        for y in range(center_y - 4, center_y + 5):
            for x in range(center_x - 4, center_x + 5):
                offset = y * msg.step + x * bytes_per_pixel
                if msg.encoding == '16UC1':
                    metres = int.from_bytes(msg.data[offset:offset + 2], 'little') / 1000.0
                else:
                    import struct
                    metres = struct.unpack_from('<f', msg.data, offset)[0]
                if 0.05 < metres < 20.0:
                    values.append(metres)

        if not values:
            self.get_logger().info('Centre depth: invalid/no-return pixels')
            return
        self.get_logger().info(
            f'Centre aligned depth: {statistics.median(values):.2f} m '
            f'({len(values)}/81 valid pixels, frame={msg.header.frame_id})'
        )


def main() -> None:
    rclpy.init()
    node = CenterDepthProbe()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        # rclpy's SIGINT handler may already have shut the context down.
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
