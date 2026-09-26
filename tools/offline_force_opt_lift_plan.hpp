#pragma once

#include "lite3_leg_kinematics.hpp"

#include <Eigen/Core>

#include <algorithm>
#include <array>
#include <cmath>
#include <stdexcept>

// Offline-only feasibility artifact. This type is intentionally not referenced
// by the validation console, state machine, hardware interface, or MotionSDK.
// It evaluates small FR lift targets on the robust-low-friction inverse-statics
// support pose without making either target executable on hardware.
class OfflineForceOptLiftPlan {
public:
    using Pose = std::array<Eigen::Vector3d,4>;

    static constexpr double kMaxJointDeltaRad = 0.03;
    static constexpr double kMaxTargetSpeedRadS = 0.10;
    static constexpr double kSupportTransitionSeconds = 5.2;
    static constexpr double kLiftTransitionSeconds = 2.0;

    OfflineForceOptLiftPlan() {
        support_ = {{
            Eigen::Vector3d( 0.00632858,-0.75172162,1.47242728),
            Eigen::Vector3d(-0.0167054439148,-0.77216783713,1.51175805905),
            Eigen::Vector3d(-0.01707707,-0.76241208,1.50300447),
            Eigen::Vector3d(-0.02225601,-0.77474549,1.48768409)}};
        lift2_ = LiftedPose(0.002);
        lift3_ = LiftedPose(0.003);
    }

    const Pose& support() const { return support_; }
    const Pose& lift2() const { return lift2_; }
    const Pose& lift3() const { return lift3_; }

    static double MaxJointDeltaFromStand(const Pose& pose) {
        const Eigen::Vector3d stand(
            0.0,-0.7729795255029084,1.5005003509817765);
        double result=0.0;
        for(const auto& q:pose)
            result=std::max(result,(q-stand).cwiseAbs().maxCoeff());
        return result;
    }

    double MaxTargetSpeed(const Pose& lifted) const {
        double lift_delta=0.0;
        for(int leg=0;leg<4;++leg)
            lift_delta=std::max(
                lift_delta,(lifted[leg]-support_[leg]).cwiseAbs().maxCoeff());
        return std::max(
            1.875*MaxJointDeltaFromStand(support_)/kSupportTransitionSeconds,
            1.875*lift_delta/kLiftTransitionSeconds);
    }

    bool WithinReviewedEnvelope(const Pose& lifted) const {
        return MaxJointDeltaFromStand(lifted)<=kMaxJointDeltaRad &&
            MaxTargetSpeed(lifted)<=kMaxTargetSpeedRadS;
    }

private:
    Pose support_{};
    Pose lift2_{};
    Pose lift3_{};

    Pose LiftedPose(double lift_m) const {
        Pose result=support_;
        const int fr=lite3::LegIndex(lite3::Leg::FR);
        Eigen::Vector3d target=lite3::FootPositionBody(
            lite3::Leg::FR,support_[fr]);
        target.z()+=lift_m;
        const auto ik=lite3::SolveFootIk(
            lite3::Leg::FR,target,support_[fr]);
        if(!ik.converged || ik.residual_m>5e-6)
            throw std::runtime_error("offline force-opt FR lift IK failed");
        result[fr]=ik.q;
        return result;
    }
};
