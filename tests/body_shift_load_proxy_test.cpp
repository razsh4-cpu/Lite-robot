#include "tools/body_shift_load_proxy.hpp"

#include <array>
#include <cmath>
#include <iostream>
#include <stdexcept>

int main() {
  try {
    const std::array<double, 12> q{{
        0.01, -0.77, 1.50, -0.01, -0.76, 1.49,
        0.02, -0.78, 1.51, -0.02, -0.75, 1.48}};
    const std::array<double, 4> expected_fz{{35.0, 42.0, 51.0, 58.0}};
    std::array<double, 12> torque{};
    for (int leg_index = 0; leg_index < 4; ++leg_index) {
      Eigen::Vector3d leg_q;
      for (int joint = 0; joint < 3; ++joint)
        leg_q[joint] = q[3 * leg_index + joint];
      const Eigen::Vector3d force(0.0, 0.0, expected_fz[leg_index]);
      const Eigen::Vector3d leg_torque =
          -lite3::NumericalJacobian(
               static_cast<lite3::Leg>(leg_index), leg_q)
               .transpose() *
          force;
      for (int joint = 0; joint < 3; ++joint)
        torque[3 * leg_index + joint] = leg_torque[joint];
    }
    const auto estimated = body_shift_load::VerticalLoadProxy(q, torque);
    for (int leg = 0; leg < 4; ++leg) {
      if (!std::isfinite(estimated[leg]) ||
          std::abs(estimated[leg] - expected_fz[leg]) > 1e-3)
        throw std::runtime_error("synthetic vertical load recovery failed");
    }
    std::cout << "body-shift load proxy inert test: PASS\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "body-shift load proxy inert test: FAIL: "
              << error.what() << '\n';
    return 1;
  }
}
