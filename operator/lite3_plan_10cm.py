#!/usr/bin/env python3
"""Plan and publish a 10 cm forward preview; never invokes navigation motion."""
import os
os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")
import json, math, time
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from nav2_msgs.action import ComputePathToPose
from nav_msgs.msg import Path
from tf2_ros import Buffer, TransformListener
from rclpy.time import Time

class Preview(Node):
    def __init__(self):
        super().__init__("lite3_plan_10cm")
        self.tf_buffer=Buffer()
        self.tf_listener=TransformListener(self.tf_buffer,self)
        self.client=ActionClient(self,ComputePathToPose,"/compute_path_to_pose")
        self.pub=self.create_publisher(Path,"/planned_path",10)

def yaw(q): return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))

def main():
    rclpy.init(); n=Preview(); deadline=time.monotonic()+10; transform=None
    while transform is None and time.monotonic()<deadline:
        rclpy.spin_once(n,timeout_sec=0.2)
        try: transform=n.tf_buffer.lookup_transform("map","base_link",Time())
        except Exception: pass
    if transform is None: raise SystemExit("PLAN FAILED: map->base_link unavailable")
    t=transform.transform; a=yaw(t.rotation)
    goal=ComputePathToPose.Goal(); goal.goal.header.frame_id="map"; goal.goal.header.stamp=n.get_clock().now().to_msg()
    goal.goal.pose.position.x=t.translation.x+0.10*math.cos(a); goal.goal.pose.position.y=t.translation.y+0.10*math.sin(a)
    goal.goal.pose.orientation=t.rotation; goal.planner_id="GridBased"; goal.use_start=False
    if not n.client.wait_for_server(timeout_sec=8): raise SystemExit("PLAN FAILED: action unavailable")
    send=n.client.send_goal_async(goal); rclpy.spin_until_future_complete(n,send,timeout_sec=8); handle=send.result()
    if handle is None or not handle.accepted: raise SystemExit("PLAN FAILED: rejected")
    result_future=handle.get_result_async(); rclpy.spin_until_future_complete(n,result_future,timeout_sec=15)
    wrapped=result_future.result(); result=wrapped.result
    if result.error_code != ComputePathToPose.Result.NONE: raise SystemExit(f"PLAN FAILED: {result.error_code} {result.error_msg}")
    n.pub.publish(result.path); rclpy.spin_once(n,timeout_sec=0.2)
    length=0.0
    for x,y in zip(result.path.poses,result.path.poses[1:]): length+=math.hypot(y.pose.position.x-x.pose.position.x,y.pose.position.y-x.pose.position.y)
    print(json.dumps({"start_x":round(t.translation.x,3),"start_y":round(t.translation.y,3),"yaw_deg":round(math.degrees(a),1),"goal_x":round(goal.goal.pose.position.x,3),"goal_y":round(goal.goal.pose.position.y,3),"path_poses":len(result.path.poses),"path_length_m":round(length,3),"error_code":int(result.error_code),"motion_sent":False},sort_keys=True))
    n.destroy_node(); rclpy.shutdown()
if __name__=="__main__": main()
