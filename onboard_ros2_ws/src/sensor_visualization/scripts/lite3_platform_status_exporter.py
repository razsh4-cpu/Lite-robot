#!/usr/bin/env python3
"""Read-only aggregation of authoritative Lite3 state."""
from __future__ import annotations
import argparse, json, math, os, re, subprocess, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

COMMANDS={"NONE","LOCAL_XBOX","LAPTOP_XBOX","AUTONOMY"}
POSTURES={"sitting":"SITTING","standing":"STANDING","standing_up":"TRANSITIONING","sitting_down":"TRANSITIONING"}
CAPS={"motion.forward":True,"motion.backward":True,"motion.lateral":True,"motion.yaw":True,"posture.control":True,"odometry":True,"localization":True,"navigation":True,"sensor.rplidar":True,"sensor.d455":True}

def finite(v,lo=None,hi=None):
    if isinstance(v,bool): return None
    try: v=float(v)
    except (TypeError,ValueError): return None
    return v if math.isfinite(v) and (lo is None or v>=lo) and (hi is None or v<=hi) else None

def sensor(available,fresh,stamp,reason):
    state="FRESH" if fresh is True else ("STALE" if fresh is False and available else "UNAVAILABLE")
    return {"available":bool(available),"ready":bool(available and fresh is True),"freshness":state,"observed_at":stamp if fresh is not None else None,"reason":None if fresh is True else reason}

def build_snapshot(source,now=None,sequence=0,stale_after=5.0):
    now=time.time() if now is None else float(now)
    bad=not isinstance(source,dict) or not source.get("robot_id")
    if bad: source={"robot_id":"unknown"}
    observed=finite(source.get("source_observed_at"),0,1e11)
    stale=observed is not None and now-observed>stale_after
    active=source.get("high_level_active"); telemetry=source.get("telemetry_fresh")
    online=active is True and telemetry is True and not stale
    if bad: health,why="UNAVAILABLE","authoritative source unavailable or malformed"
    elif stale: health,why="STALE","authoritative observation is stale"
    elif online: health,why="READY",None
    elif active is True: health,why="DEGRADED","HIGH-LEVEL active but telemetry unavailable"
    elif active is False: health,why="OFFLINE","HIGH-LEVEL runtime inactive"
    else: health,why="UNAVAILABLE","HIGH-LEVEL state unavailable"
    if stale: posture="STALE"
    elif telemetry is False: posture="OFFLINE"
    else: posture=POSTURES.get(str(source.get("posture","")).lower(),"UNAVAILABLE")
    high="STALE" if stale else ("READY" if online else ("DEGRADED" if active is True else ("OFFLINE" if active is False else "UNAVAILABLE")))
    loc=str(source.get("localization_state","UNAVAILABLE")).upper()
    if loc not in {"LOCALIZED","UNLOCALIZED","STARTING","FAILED","STALE","UNAVAILABLE","OFFLINE","UNKNOWN"}: loc="UNKNOWN"
    if stale: loc="STALE"
    score=finite(source.get("localization_confidence"),0,1)
    loc_ready=not stale and online and source.get("localization_ready") is True and loc=="LOCALIZED"
    loc_reason=source.get("localization_reason") or (None if loc_ready else "localization not ready")
    nav_avail=source.get("nav2_available") is True
    nav_ready=not stale and online and nav_avail and source.get("nav2_ready") is True and loc_ready
    nav=str(source.get("nav2_state","UNAVAILABLE")).upper()
    if nav not in {"IDLE","ACTIVE","SUCCEEDED","FAILED","CANCELLED","STALE","UNAVAILABLE","OFFLINE","UNKNOWN"}: nav="UNKNOWN"
    if stale: nav="STALE"
    command=str(source.get("command_source","UNKNOWN")).upper()
    if stale: command="STALE"
    elif command not in COMMANDS: command="UNKNOWN"
    watchdog=str(source.get("watchdog_state","UNAVAILABLE")).upper()
    if watchdog not in {"OK","TRIPPED","STALE","UNAVAILABLE","OFFLINE","UNKNOWN"}: watchdog="UNKNOWN"
    if stale: watchdog="STALE"
    required_inputs=(posture=="STANDING" and finite(source.get("battery_percent"),0,100) is not None
                     and source.get("rplidar_fresh") is True
                     and source.get("odometry_fresh") is True
                     and source.get("tf_fresh") is True)
    safe=online and command=="NONE" and watchdog=="OK" and not stale and required_inputs
    refusal=source.get("refusal_reason") or (None if safe else why or "platform safety not ready")
    stamp=observed
    sensors={
      "rplidar":sensor(source.get("rplidar_available") is True,source.get("rplidar_fresh"),stamp,"LiDAR scan unavailable or stale"),
      "d455":sensor(source.get("d455_available") is True,source.get("d455_fresh"),stamp,"D455 stream unavailable or stale"),
      "odometry":sensor(source.get("odometry_available") is True,source.get("odometry_fresh"),stamp,"odometry unavailable or stale"),
      "tf":sensor(source.get("tf_available") is True,source.get("tf_fresh"),stamp,"required TF unavailable or stale")}
    if stale:
      for v in sensors.values(): v.update(ready=False,freshness="STALE",reason="authoritative observation is stale")
    return {"schema":"robot.platform_status","schema_version":1,"robot_id":str(source.get("robot_id") or "unknown"),"platform_type":"bipolix.lite3","interface_version":"1.0","observed_at":observed or now,"published_at":now,"sequence":max(0,int(sequence)),
      "connectivity":{"online":online,"gateway_health":health,"gateway_reason":why},
      "robot_state":{"posture":posture,"battery_percent":finite(source.get("battery_percent"),0,100),"high_level_health":high},"capabilities":dict(CAPS),
      "localization":{"state":loc,"confidence":score,"active_map":source.get("active_map") or None,"ready":loc_ready,"reason":loc_reason,"observed_at":stamp},
      "navigation":{"available":nav_avail,"ready":nav_ready,"state":nav,"reason":source.get("nav2_reason") or (None if nav_ready else "navigation not ready"),"observed_at":stamp},
      "sensors":sensors,"safety":{"command_source":command,"robot_side_owner":source.get("robot_side_owner") or None,"safety_ready":safe,"watchdog_state":watchdog,"refusal_reason":refusal,"motion_commands_supported":False}}

def atomic_write_json(path,payload):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); temp=path.with_name(f".{path.name}.{os.getpid()}")
    try: temp.write_text(json.dumps(payload,sort_keys=True)+"\n",encoding="utf-8"); os.replace(temp,path)
    finally:
      try: temp.unlink()
      except FileNotFoundError: pass

class HostProbe:
  def __init__(self,robot_id="robot_01",state_dir="/run/lite3-control",timeout=2.0,clock=None): self.robot_id=robot_id; self.state_dir=Path(state_dir); self.timeout=timeout; self.clock=clock or time.time
  def run(self,args):
    try:
      p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=self.timeout,check=False); return p.stdout.strip() if p.returncode==0 else None
    except (OSError,subprocess.TimeoutExpired): return None
  def active(self,u): return self.run(["systemctl","is-active",u])=="active"
  def available(self,u): return self.run(["systemctl","show","-p","LoadState","--value",u]) not in (None,"not-found")
  def read(self,n):
    try:return (self.state_dir/n).read_text(encoding="utf-8").strip()
    except OSError:return None
  def topic(self,t,field="data",reliability="best_effort"): return self.run(["timeout",str(self.timeout),"ros2","topic","echo",t,"--once","--field",field,"--qos-reliability",reliability,"--qos-durability","volatile"])
  def tf(self,a,b):
    v=self.run(["timeout",str(self.timeout),"ros2","run","tf2_ros","tf2_echo",a,b]); return v is not None and "Translation:" in v
  def posture(self,now):
    v=self.run(["journalctl","-u","lite3-high-level-runtime.service","-n","80","--no-pager","-o","json"])
    for line in reversed((v or "").splitlines()):
      try:
        j=json.loads(line); m=re.search(r"robot_status=([a-z0-9_]+).*telemetry_fresh=(true|false)",j.get("MESSAGE","")); stamp=float(j.get("__REALTIME_TIMESTAMP",0))/1e6
      except (ValueError,TypeError,json.JSONDecodeError): continue
      if m:return m.group(1),m.group(2)=="true" and now-stamp<=15
    return None,False
  def collect(self):
    now=self.clock(); calls={"high":(self.active,"lite3-high-level-runtime.service"),"la":(self.available,"lite3-lidar.service"),"da":(self.available,"lite3-realsense.service"),"na":(self.available,"lite3-nav2.service"),"nav":(self.active,"lite3-nav2.service"),"odom":(self.topic,"/odom","header.stamp"),"scan":(self.topic,"/scan","header.stamp"),"d455":(self.topic,"/camera/camera/color/image_raw","header.stamp"),"bat":(self.topic,"/lite3/battery_percent"),"to":(self.tf,"odom","base_link"),"tl":(self.tf,"base_link","lidar_link"),"tm":(self.tf,"map","base_link"),"posture":(self.posture,now)}
    with ThreadPoolExecutor(max_workers=len(calls)) as ex: vals={k:ex.submit(fn,*args) for k,(fn,*args) in calls.items()}; vals={k:v.result() for k,v in vals.items()}
    posture,telemetry=vals["posture"]; loc=self.read("LOCALIZATION_STATE") or "UNAVAILABLE"; score=finite(self.read("LOCALIZATION_SCORE"),0,1); startup=self.read("LOCALIZATION_STARTUP_STATE") or "UNKNOWN"; error=self.read("LOCALIZATION_STARTUP_ERROR") or None; command=self.read("COMMAND_SOURCE") or "UNKNOWN"; odom=vals["odom"] is not None; tf=vals["to"] and vals["tl"]; lr=loc.upper()=="LOCALIZED" and score is not None and score>=.8 and vals["tm"]
    return {"robot_id":self.robot_id,"high_level_active":vals["high"],"telemetry_fresh":telemetry and odom,"posture":posture,"battery_percent":finite(str(vals["bat"] or "").strip("' \n"),0,100),"command_source":command,"robot_side_owner":None,"watchdog_state":"OK" if vals["high"] and telemetry and odom else "UNAVAILABLE","localization_state":loc,"localization_confidence":score,"localization_ready":bool(lr),"localization_reason":error,"active_map":self.read("ACTIVE_MAP"),"nav2_available":vals["na"],"nav2_ready":bool(vals["nav"] and startup=="NAVIGATION_READY" and lr),"nav2_state":"IDLE" if vals["nav"] and lr else "UNAVAILABLE","nav2_reason":None if vals["nav"] and lr else f"startup={startup}","rplidar_available":vals["la"],"rplidar_fresh":vals["scan"] is not None,"d455_available":vals["da"],"d455_fresh":vals["d455"] is not None,"odometry_available":vals["high"],"odometry_fresh":odom,"tf_available":True,"tf_fresh":bool(tf),"refusal_reason":None if vals["high"] and telemetry and odom else "HIGH-LEVEL telemetry unavailable or stale","source_observed_at":now}

def main(argv=None):
  p=argparse.ArgumentParser(); p.add_argument("--robot-id",default=os.getenv("LITE3_ROBOT_ID","robot_01")); p.add_argument("--state-dir",default="/run/lite3-control"); p.add_argument("--output",default="/run/lite3-control/platform_status.json"); p.add_argument("--interval",type=float,default=2); p.add_argument("--once",action="store_true"); a=p.parse_args(argv); probe=HostProbe(a.robot_id,a.state_dir); seq=int(time.time()*1000)
  while True:
    now=time.time()
    try: source=probe.collect()
    except Exception as e: source={"robot_id":a.robot_id,"refusal_reason":f"probe failure: {type(e).__name__}","source_observed_at":now}
    atomic_write_json(a.output,build_snapshot(source,now,seq)); seq+=1
    if a.once:return 0
    time.sleep(max(.2,a.interval))
if __name__=="__main__": raise SystemExit(main())
