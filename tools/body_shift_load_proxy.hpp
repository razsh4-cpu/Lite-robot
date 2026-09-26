#pragma once

#include "lite3_leg_kinematics.hpp"

#include <Eigen/Cholesky>
#include <Eigen/Core>

#include <array>
#include <cmath>
#include <stdexcept>

namespace body_shift_load {

inline constexpr double kDamping = 1e-4;

// Relative load estimator only. Motor torque also contains leg gravity,
// friction, actuator bias and dynamics, so callers must subtract a stable-stand
// baseline and must not treat the result as calibrated contact force.
inline std::array<double, 4> VerticalLoadProxy(
    const std::array<double, 12>& q,
    const std::array<double, 12>& torque) {
  std::array<double, 4> result{};
  for (int leg_index = 0; leg_index < 4; ++leg_index) {
    const auto leg = static_cast<lite3::Leg>(leg_index);
    Eigen::Vector3d leg_q;
    Eigen::Vector3d leg_torque;
    for (int joint = 0; joint < 3; ++joint) {
      leg_q[joint] = q[3 * leg_index + joint];
      leg_torque[joint] = torque[3 * leg_index + joint];
    }
    if (!leg_q.allFinite() || !leg_torque.allFinite())
      throw std::runtime_error("non-finite joint sample");

    const Eigen::Matrix3d jacobian = lite3::NumericalJacobian(leg, leg_q);
    // Damped least squares for J^T F = -tau.
    const Eigen::Matrix3d a = jacobian.transpose();
    const Eigen::Vector3d force =
        (a.transpose() * a +
         kDamping * kDamping * Eigen::Matrix3d::Identity())
            .ldlt()
            .solve(a.transpose() * (-leg_torque));
    if (!force.allFinite())
      throw std::runtime_error("non-finite load estimate");
    result[leg_index] = force.z();
  }
  return result;
}

}  // namespace body_shift_load
