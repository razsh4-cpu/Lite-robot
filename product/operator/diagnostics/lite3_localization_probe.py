#!/usr/bin/env python3
"""Read-only local grid search around AMCL pose; publishes nothing."""
import json
import math
import time

import numpy as np
from scipy.ndimage import distance_transform_edt
import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import OccupancyGrid
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformException, TransformListener


def yaw(q):
    return math.atan2(2.0*(q.w*q.z+q.x*q.y), 1.0-2.0*(q.y*q.y+q.z*q.z))


class Probe(Node):
    def __init__(self):
        super().__init__("lite3_localization_probe")
        latched=QoSProfile(depth=1)
        latched.reliability=ReliabilityPolicy.RELIABLE
        latched.durability=DurabilityPolicy.TRANSIENT_LOCAL
        self.map=self.scan=self.pose=None
        self.create_subscription(OccupancyGrid,"/map",lambda m:setattr(self,"map",m),latched)
        self.create_subscription(PoseWithCovarianceStamped,"/amcl_pose",lambda m:setattr(self,"pose",m),latched)
        self.create_subscription(LaserScan,"/scan",lambda m:setattr(self,"scan",m),qos_profile_sensor_data)
        self.tf=Buffer(); self.listener=TransformListener(self.tf,self)

    def run(self):
        deadline=time.monotonic()+15
        tr=None
        while time.monotonic()<deadline:
            rclpy.spin_once(self,timeout_sec=0.2)
            if self.map is not None and self.scan is not None and self.pose is not None:
                try:
                    tr=self.tf.lookup_transform("base_link",self.scan.header.frame_id,rclpy.time.Time(),timeout=Duration(seconds=0.1)); break
                except TransformException: pass
        if tr is None: raise RuntimeError("map/scan/amcl_pose/TF unavailable")
        info=self.map.info; grid=np.asarray(self.map.data,dtype=np.int16).reshape(info.height,info.width)
        distance=distance_transform_edt(grid<65)*float(info.resolution)
        idx=np.arange(0,len(self.scan.ranges),8); ranges=np.asarray(self.scan.ranges,dtype=float)[idx]
        angles=float(self.scan.angle_min)+idx*float(self.scan.angle_increment)
        valid=np.isfinite(ranges)&(ranges>self.scan.range_min)&(ranges<np.minimum(self.scan.range_max,12.0))
        ranges=ranges[valid]; angles=angles[valid]
        lxy=np.vstack((ranges*np.cos(angles),ranges*np.sin(angles)))
        lt=tr.transform.translation; lyaw=yaw(tr.transform.rotation)
        rot=np.array([[math.cos(lyaw),-math.sin(lyaw)],[math.sin(lyaw),math.cos(lyaw)]])
        bxy=rot@lxy+np.array([[lt.x],[lt.y]])
        origin=np.array([info.origin.position.x,info.origin.position.y]); oyaw=yaw(info.origin.orientation)
        inv=np.array([[math.cos(oyaw),math.sin(oyaw)],[-math.sin(oyaw),math.cos(oyaw)]])
        p=self.pose.pose.pose; base=(p.position.x,p.position.y,yaw(p.orientation))
        def score(x,y,a):
            r=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
            world=r@bxy+np.array([[x],[y]])
            local=inv@(world-origin[:,None]); gx=(local[0]/info.resolution).astype(int); gy=(local[1]/info.resolution).astype(int)
            inside=(gx>=0)&(gx<info.width)&(gy>=0)&(gy<info.height)
            hit=np.zeros(gx.shape,dtype=bool); hit[inside]=distance[gy[inside],gx[inside]]<=0.15
            return float(hit.mean()),int(hit.sum()),len(hit)
        current=score(*base); best=(current[0],0.0,0.0,0.0,current[1],current[2])
        for da in np.deg2rad(np.arange(-15.0,15.01,1.5)):
            for dx in np.arange(-0.25,0.251,0.025):
                for dy in np.arange(-0.25,0.251,0.025):
                    s,h,n=score(base[0]+dx,base[1]+dy,base[2]+da)
                    if s>best[0]: best=(s,float(dx),float(dy),float(da),h,n)
        print(json.dumps({"current_score":round(current[0],3),"best_score":round(best[0],3),"offset_x_m":round(best[1],3),"offset_y_m":round(best[2],3),"offset_yaw_deg":round(math.degrees(best[3]),1),"suggested_x":round(base[0]+best[1],6),"suggested_y":round(base[1]+best[2],6),"suggested_yaw":round(base[2]+best[3],6),"hits":best[4],"points":best[5]},sort_keys=True))


def main():
    rclpy.init(); node=Probe()
    try: node.run()
    finally:
        node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()
if __name__=="__main__": main()
