#!/usr/bin/env python3
"""Execute one approved 10 cm Nav2 goal with bounded monitoring."""
import os
os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")
from pathlib import Path
import json, math, time
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from geometry_msgs.msg import Twist
from nav2_msgs.action import NavigateToPose
from tf2_ros import Buffer, TransformListener

SOURCE=Path('/run/lite3-control/COMMAND_SOURCE')
def owner():
    try: return SOURCE.read_text().strip()
    except OSError: return 'UNKNOWN'
def yaw(q): return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))

class Execute(Node):
    def __init__(self):
        super().__init__('lite3_execute_10cm')
        self.tf_buffer=Buffer(); self.tf_listener=TransformListener(self.tf_buffer,self)
        self.client=ActionClient(self,NavigateToPose,'/navigate_to_pose')
        self.max_cmd=[0.0,0.0,0.0]; self.last_feedback=None
        self.create_subscription(Twist,'/cmd_vel',self.cmd,qos_profile_sensor_data)
    def cmd(self,m):
        self.max_cmd=[max(self.max_cmd[0],abs(m.linear.x)),max(self.max_cmd[1],abs(m.linear.y)),max(self.max_cmd[2],abs(m.angular.z))]
    def feedback(self,m): self.last_feedback=float(m.feedback.distance_remaining)
    def transform(self,timeout=8.0):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            rclpy.spin_once(self,timeout_sec=0.1)
            try: return self.tf_buffer.lookup_transform('map','base_link',Time())
            except Exception: pass
        return None

def main():
    if owner()!='AUTONOMY': raise SystemExit(f'EXECUTION BLOCKED: COMMAND_SOURCE={owner()}')
    rclpy.init(); n=Execute()
    try:
        start=n.transform()
        if start is None: raise SystemExit('EXECUTION BLOCKED: map->base_link unavailable')
        t=start.transform; a=yaw(t.rotation)
        goal=NavigateToPose.Goal(); goal.pose.header.frame_id='map'; goal.pose.header.stamp=n.get_clock().now().to_msg()
        goal.pose.pose.position.x=t.translation.x+0.10*math.cos(a); goal.pose.pose.position.y=t.translation.y+0.10*math.sin(a); goal.pose.pose.orientation=t.rotation
        if not n.client.wait_for_server(timeout_sec=5): raise SystemExit('EXECUTION BLOCKED: navigate action unavailable')
        future=n.client.send_goal_async(goal,feedback_callback=n.feedback); rclpy.spin_until_future_complete(n,future,timeout_sec=5)
        handle=future.result()
        if handle is None or not handle.accepted: raise SystemExit('EXECUTION BLOCKED: goal rejected')
        result=handle.get_result_async(); deadline=time.monotonic()+20.0
        while not result.done() and time.monotonic()<deadline:
            rclpy.spin_once(n,timeout_sec=0.05)
            if owner()!='AUTONOMY':
                handle.cancel_goal_async(); raise SystemExit(f'EXECUTION ABORTED: COMMAND_SOURCE={owner()}')
        if not result.done():
            cancel=handle.cancel_goal_async(); rclpy.spin_until_future_complete(n,cancel,timeout_sec=3)
            raise SystemExit('EXECUTION ABORTED: 20s timeout')
        wrapped=result.result(); end=n.transform(3.0)
        if end is None: raise SystemExit('EXECUTION ABORTED: final TF unavailable')
        e=end.transform
        distance=math.hypot(e.translation.x-t.translation.x,e.translation.y-t.translation.y)
        print(json.dumps({'action_status':int(wrapped.status),'start_x':round(t.translation.x,3),'start_y':round(t.translation.y,3),'goal_x':round(goal.pose.pose.position.x,3),'goal_y':round(goal.pose.pose.position.y,3),'end_x':round(e.translation.x,3),'end_y':round(e.translation.y,3),'measured_displacement_m':round(distance,3),'max_cmd_vx':round(n.max_cmd[0],3),'max_cmd_vy':round(n.max_cmd[1],3),'max_cmd_wz':round(n.max_cmd[2],3),'last_distance_remaining':None if n.last_feedback is None else round(n.last_feedback,3)},sort_keys=True))
        if wrapped.status != 4: raise SystemExit(f'GOAL FAILED: action status {wrapped.status}')
    finally:
        n.destroy_node(); rclpy.shutdown()
if __name__=='__main__': main()
