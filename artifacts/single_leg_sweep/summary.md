# Lite3 FR Single-Leg Simulation Sweep

Mode: **smoke**
Total simulations: **15**

This is simulation-only evidence. It does not approve hardware gains or motion.

## Acceptance

- Minimum success rate: 95%
- Clearance: >= 5.0 mm
- Clear-margin clearance: >= 6.0 mm
- Clear support margin: >= 20.0 mm
- Touchdown speed: <= 0.200 m/s
- Final joint error: <= 0.100 rad

## Top candidates

### 1. Candidate 0

- Success: 0/5 (0.0%)
- Shift: X=60 mm, Y=60 mm
- Shift/hold: 2.0 s / 0.0 s
- Lift: 15 mm over 1.5 s
- Lower: 1.5 s
- PD: kp=180, kd=3.5
- Worst support margin: 93.58 mm
- Worst clearance: 0.00 mm
- Worst roll/pitch: 0.49 / 0.80 deg
- Worst torque: 30.00 Nm
- Worst touchdown speed: 1.623 m/s
- Clear margin: NO

### 2. Candidate 1

- Success: 0/5 (0.0%)
- Shift: X=55 mm, Y=55 mm
- Shift/hold: 2.5 s / 0.5 s
- Lift: 15 mm over 1.75 s
- Lower: 1.75 s
- PD: kp=170, kd=3.5
- Worst support margin: nan mm
- Worst clearance: 0.00 mm
- Worst roll/pitch: 0.00 / 0.00 deg
- Worst torque: 30.00 Nm
- Worst touchdown speed: 0.000 m/s
- Clear margin: NO

### 3. Candidate 2

- Success: 0/5 (0.0%)
- Shift: X=65 mm, Y=60 mm
- Shift/hold: 2.5 s / 0.5 s
- Lift: 17 mm over 2.0 s
- Lower: 2.0 s
- PD: kp=180, kd=4.0
- Worst support margin: nan mm
- Worst clearance: 0.00 mm
- Worst roll/pitch: 0.00 / 0.00 deg
- Worst torque: 30.00 Nm
- Worst touchdown speed: 0.000 m/s
- Clear margin: NO

## Selection gate

No candidate currently satisfies both >=95% success and the configured clear-margin gate.

## Remaining sim-to-real gaps

- Payload model is represented as additional torso mass, not a measured payload inertia model.
- CoM uncertainty ranges are simulation assumptions, not measured Lite3 identification data.
- Contact friction/compliance ranges are not calibrated against the real floor/feet.
- Joint-zero, sensor-noise and delay ranges are not yet based on hardware characterization.
- Motor/gearbox dynamics, backlash, battery-voltage effects and thermal effects are not identified here.
- Simulation success must therefore not be interpreted as permission to copy these parameters directly to hardware.
