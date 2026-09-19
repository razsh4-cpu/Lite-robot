#pragma once

#include "../tools/lite3_leg_kinematics.hpp"

#include <Eigen/Core>

#include <algorithm>
#include <array>
#include <cmath>
#include <stdexcept>

// A deterministic, position-only trajectory for one mechanically supported
// validation run. This class has no transport and cannot send robot commands.
class SupportedLegLiftPlan {
public:
    enum class Phase {
        ShiftBody,
        HoldShift,
        LiftFrontRight,
        HoldFrontRight,
        LowerFrontRight,
        RecenterBody,
        Complete,
    };

    struct Sample {
        Eigen::Matrix<float, 12, 5> command = Eigen::Matrix<float, 12, 5>::Zero();
        Phase phase = Phase::ShiftBody;
        bool complete = false;
    };

    static constexpr double kBodyShiftM = 0.005;
    static constexpr double kFootLiftM = 0.040;
    static constexpr double kShiftSeconds = 2.0;
    static constexpr double kShiftHoldSeconds = 1.0;
    static constexpr double kLiftSeconds = 1.0;
    static constexpr double kLiftHoldSeconds = 0.5;
    static constexpr double kLowerSeconds = 1.0;
    static constexpr double kRecenterSeconds = 3.0;
    static constexpr double kTotalSeconds = kShiftSeconds + kShiftHoldSeconds +
        kLiftSeconds + kLiftHoldSeconds + kLowerSeconds + kRecenterSeconds;
    static constexpr float kKp = 60.0f;
    static constexpr float kKd = 0.7f;

    SupportedLegLiftPlan() {
        constexpr double thigh = 0.20;
        constexpr double shank = 0.21;
        constexpr double height = 0.30;
        constexpr double pi = 3.14159265358979323846;
        const double hip = -std::acos((thigh * thigh + height * height - shank * shank) /
                                      (2.0 * thigh * height));
        const double knee = pi - std::acos((thigh * thigh + shank * shank - height * height) /
                                           (2.0 * thigh * shank));
        const Eigen::Vector3d stand(0.0, hip, knee);
        for (int leg_index = 0; leg_index < 4; ++leg_index) {
            const auto leg = static_cast<lite3::Leg>(leg_index);
            stand_[leg_index] = stand;
            const auto nominal = lite3::FootPositionBody(leg, stand);
            const Eigen::Vector3d shifted_target =
                nominal + Eigen::Vector3d(0.005, -0.005, 0.0);
            const auto shifted = lite3::SolveFootIk(leg, shifted_target, stand);
            if (!shifted.converged || shifted.residual_m > 5e-6)
                throw std::runtime_error("supported leg test shift IK failed");
            shifted_[leg_index] = shifted.q;
            Eigen::Vector3d lift_target = shifted_target;
            if (leg == lite3::Leg::FR) lift_target.z() += kFootLiftM;
            const auto lifted = lite3::SolveFootIk(leg, lift_target, shifted.q);
            if (!lifted.converged || lifted.residual_m > 5e-6)
                throw std::runtime_error("supported leg test lift IK failed");
            lifted_[leg_index] = lifted.q;
        }
    }

    Sample At(double elapsed_seconds) const {
        const double elapsed = std::max(0.0, elapsed_seconds);
        if (elapsed < kShiftSeconds)
            return Interpolate(stand_, shifted_, elapsed / kShiftSeconds,
                               kShiftSeconds, Phase::ShiftBody);
        double t = elapsed - kShiftSeconds;
        if (t < kShiftHoldSeconds) return Hold(shifted_, Phase::HoldShift);
        t -= kShiftHoldSeconds;
        if (t < kLiftSeconds)
            return Interpolate(shifted_, lifted_, t / kLiftSeconds,
                               kLiftSeconds, Phase::LiftFrontRight);
        t -= kLiftSeconds;
        if (t < kLiftHoldSeconds) return Hold(lifted_, Phase::HoldFrontRight);
        t -= kLiftHoldSeconds;
        if (t < kLowerSeconds)
            return Interpolate(lifted_, shifted_, t / kLowerSeconds,
                               kLowerSeconds, Phase::LowerFrontRight);
        t -= kLowerSeconds;
        if (t < kRecenterSeconds)
            return Interpolate(shifted_, stand_, t / kRecenterSeconds,
                               kRecenterSeconds, Phase::RecenterBody);
        auto sample = Hold(stand_, Phase::Complete);
        sample.complete = true;
        return sample;
    }

    const std::array<Eigen::Vector3d, 4>& stand() const { return stand_; }
    const std::array<Eigen::Vector3d, 4>& shifted() const { return shifted_; }
    const std::array<Eigen::Vector3d, 4>& lifted() const { return lifted_; }

private:
    using Pose = std::array<Eigen::Vector3d, 4>;
    Pose stand_{}, shifted_{}, lifted_{};

    static double QuinticDerivative(double phase) {
        const double s = std::clamp(phase, 0.0, 1.0);
        return 30.0 * s * s * (1.0 - s) * (1.0 - s);
    }

    static Sample Interpolate(const Pose& from, const Pose& to, double phase,
                              double duration, Phase state) {
        const double blend = lite3::Quintic(phase);
        const double blend_velocity = QuinticDerivative(phase) / duration;
        Sample result;
        result.phase = state;
        for (int leg = 0; leg < 4; ++leg) {
            const Eigen::Vector3d q = from[leg] + blend * (to[leg] - from[leg]);
            const Eigen::Vector3d dq = blend_velocity * (to[leg] - from[leg]);
            for (int joint = 0; joint < 3; ++joint) {
                const int index = 3 * leg + joint;
                result.command(index, 0) = kKp;
                result.command(index, 1) = static_cast<float>(q[joint]);
                result.command(index, 2) = kKd;
                result.command(index, 3) = static_cast<float>(dq[joint]);
                result.command(index, 4) = 0.0f;
            }
        }
        return result;
    }

    static Sample Hold(const Pose& pose, Phase state) {
        return Interpolate(pose, pose, 0.0, 1.0, state);
    }
};
