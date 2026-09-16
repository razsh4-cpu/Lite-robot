#include "control_parameters.h"

void ControlParameters::GenerateLite3Parameters(){
    body_len_x_ = 0.1745*2;
    body_len_y_ = 0.062*2;
    hip_len_ = 0.0985;
    thigh_len_ = 0.20;
    shank_len_ = 0.21;

    pre_height_ = 0.12;
    // Keep the stand endpoint paired with the restored pre-April policy.
    // Vendor commit 7871b47 changed this from 0.30 to 0.33 in the same
    // change that replaced the policy and its -0.80/1.60 default pose.
    stand_height_ = 0.30;
    swing_leg_kp_ << 100., 100., 100.;
    swing_leg_kd_ << 2.5, 2.5, 2.5;
    // swing_leg_kp_ << 180., 180., 180.;
    // swing_leg_kd_ << 3.5, 3.5, 3.5;

    fl_joint_lower_ << -0.530, -3.50, 0.349;
    fl_joint_upper_ << 0.530, 0.320, 2.80;
    joint_vel_limit_ << 30, 30, 20;
    torque_limit_ << 40, 40, 65;
}
