#include "tools/lite3_leg_kinematics.hpp"

#include <cmath>
#include <iostream>

namespace {

bool Near(double actual, double expected, double tolerance) {
  if (std::abs(actual - expected) <= tolerance) return true;
  std::cerr << "expected " << expected << ", got " << actual << "\n";
  return false;
}

}  // namespace

int main() {
  using lite3::Leg;
  const Eigen::Vector3d stand(0.0, -0.7729795255029084, 1.5005003509817765);
  const Eigen::Vector3d fl = lite3::FootPositionBody(Leg::FL, stand);
  const Eigen::Vector3d fr = lite3::FootPositionBody(Leg::FR, stand);

  if (!Near(fl.x(), fr.x(), 1e-12) || !Near(fl.y(), -fr.y(), 1e-12) ||
      !Near(fl.z(), fr.z(), 1e-12) || !Near(fl.z(), -0.30, 2e-4)) {
    return 1;
  }

  for (lite3::Leg leg : {Leg::FL, Leg::FR, Leg::HL, Leg::HR}) {
    const Eigen::Vector3d initial = lite3::FootPositionBody(leg, stand);
    for (const Eigen::Vector3d delta : {
             Eigen::Vector3d(0.060, -0.060, 0.0),
             Eigen::Vector3d(0.060, -0.060, 0.015),
             Eigen::Vector3d(0.065, -0.060, 0.015)}) {
      const auto ik = lite3::SolveFootIk(leg, initial + delta, stand);
      if (!ik.converged || ik.residual_m > 5e-6) {
        std::cerr << lite3::kLegNames[lite3::LegIndex(leg)]
                  << " IK residual " << ik.residual_m << "\n";
        return 2;
      }
      const Eigen::Vector3d reconstructed = lite3::FootPositionBody(leg, ik.q);
      if ((reconstructed - (initial + delta)).norm() > 5e-6) return 3;
      if ((ik.q.array() < lite3::LowerLimits().array()).any() ||
          (ik.q.array() > lite3::UpperLimits().array()).any()) return 4;
    }
  }

  std::cout << "Lite3 FK/IK checks passed\n";
  return 0;
}
