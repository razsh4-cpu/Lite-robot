#pragma once

#include <Eigen/Core>
#include <Eigen/Geometry>

#include <algorithm>
#include <array>
#include <cmath>
#include <string>

namespace lite3 {

enum class Leg : int { FL = 0, FR = 1, HL = 2, HR = 3 };

inline constexpr std::array<const char*, 4> kLegNames{"FL", "FR", "HL", "HR"};
inline constexpr std::array<const char*, 3> kJointNames{"HipX", "HipY", "Knee"};

struct LegGeometry {
  double body_half_length = 0.1745;
  double body_half_width = 0.062;
  double hip_offset = 0.09735;
  double thigh_length = 0.20;
  double shank_length = 0.21012;
};

inline int LegIndex(Leg leg) { return static_cast<int>(leg); }
inline int SdkIndex(Leg leg, int joint_in_leg) {
  return 3 * LegIndex(leg) + joint_in_leg;
}
inline bool IsFront(Leg leg) { return leg == Leg::FL || leg == Leg::FR; }
inline bool IsLeft(Leg leg) { return leg == Leg::FL || leg == Leg::HL; }

inline Eigen::Vector3d HipOrigin(Leg leg, const LegGeometry& geometry = {}) {
  return {IsFront(leg) ? geometry.body_half_length : -geometry.body_half_length,
          IsLeft(leg) ? geometry.body_half_width : -geometry.body_half_width,
          0.0};
}

// Exact transform chain encoded in Lite3.xml. Joint axes are -X, -Y, -Y.
inline Eigen::Vector3d FootPositionBody(
    Leg leg, const Eigen::Vector3d& q, const LegGeometry& geometry = {}) {
  const Eigen::Vector3d axis_x(-1.0, 0.0, 0.0);
  const Eigen::Vector3d axis_y(0.0, -1.0, 0.0);
  Eigen::Matrix3d rotation = Eigen::AngleAxisd(q[0], axis_x).toRotationMatrix();
  Eigen::Vector3d position = HipOrigin(leg, geometry);
  position += rotation * Eigen::Vector3d(
      0.0, IsLeft(leg) ? geometry.hip_offset : -geometry.hip_offset, 0.0);
  rotation *= Eigen::AngleAxisd(q[1], axis_y).toRotationMatrix();
  position += rotation * Eigen::Vector3d(0.0, 0.0, -geometry.thigh_length);
  rotation *= Eigen::AngleAxisd(q[2], axis_y).toRotationMatrix();
  position += rotation * Eigen::Vector3d(0.0, 0.0, -geometry.shank_length);
  return position;
}

inline Eigen::Matrix3d NumericalJacobian(
    Leg leg, const Eigen::Vector3d& q, const LegGeometry& geometry = {}) {
  constexpr double kEpsilon = 1e-6;
  Eigen::Matrix3d jacobian;
  for (int column = 0; column < 3; ++column) {
    Eigen::Vector3d upper = q;
    Eigen::Vector3d lower = q;
    upper[column] += kEpsilon;
    lower[column] -= kEpsilon;
    jacobian.col(column) =
        (FootPositionBody(leg, upper, geometry) -
         FootPositionBody(leg, lower, geometry)) /
        (2.0 * kEpsilon);
  }
  return jacobian;
}

inline Eigen::Vector3d LowerLimits() { return {-0.523, -2.67, 0.524}; }
inline Eigen::Vector3d UpperLimits() { return {0.523, 0.314, 2.792}; }

struct IkResult {
  Eigen::Vector3d q = Eigen::Vector3d::Zero();
  double residual_m = 0.0;
  int iterations = 0;
  bool converged = false;
};

// Damped least-squares Cartesian IK using the exact model transform chain.
// The seed selects the nearby knee-bent solution and every iteration enforces
// the limits declared by Lite3.xml.
inline IkResult SolveFootIk(Leg leg, const Eigen::Vector3d& target,
                            const Eigen::Vector3d& seed,
                            const LegGeometry& geometry = {}) {
  constexpr int kMaxIterations = 80;
  constexpr double kToleranceM = 1e-7;
  constexpr double kDamping = 1e-5;
  constexpr double kMaxJointStep = 0.08;
  const Eigen::Vector3d lower = LowerLimits();
  const Eigen::Vector3d upper = UpperLimits();

  IkResult result;
  result.q = seed.cwiseMax(lower).cwiseMin(upper);
  for (int iteration = 0; iteration < kMaxIterations; ++iteration) {
    const Eigen::Vector3d error = target - FootPositionBody(leg, result.q, geometry);
    result.residual_m = error.norm();
    result.iterations = iteration + 1;
    if (result.residual_m <= kToleranceM) {
      result.converged = true;
      return result;
    }
    const Eigen::Matrix3d jacobian = NumericalJacobian(leg, result.q, geometry);
    Eigen::Vector3d step = jacobian.transpose() *
        (jacobian * jacobian.transpose() +
         kDamping * Eigen::Matrix3d::Identity()).ldlt().solve(error);
    const double largest = step.cwiseAbs().maxCoeff();
    if (largest > kMaxJointStep) step *= kMaxJointStep / largest;
    result.q = (result.q + step).cwiseMax(lower).cwiseMin(upper);
  }
  result.residual_m = (target - FootPositionBody(leg, result.q, geometry)).norm();
  result.converged = result.residual_m <= 5e-6;
  return result;
}

inline double Quintic(double phase) {
  const double s = std::clamp(phase, 0.0, 1.0);
  return s * s * s * (10.0 + s * (-15.0 + 6.0 * s));
}

}  // namespace lite3
