#pragma once

#include "supported_leg_lift_plan.hpp"

#include <Eigen/Core>

#include <algorithm>
#include <array>
#include <cmath>

// Offline-only command generator for the prerequisite supported body-shift.
// It has no SDK or transport dependency.  It deliberately never lifts a foot.
class SupportedBodyShiftPlan {
public:
    enum class GainStrategy { AbruptReduced, KeepStand, SmoothReduced };
    enum class Phase { ShiftWeight, HoldShift, Recenter, Complete };

    struct Sample {
        Eigen::Matrix<float, 12, 5> command = Eigen::Matrix<float, 12, 5>::Zero();
        Phase phase{Phase::ShiftWeight};
        bool complete{false};
    };

    static constexpr double kShiftM = 0.005;
    static constexpr double kShiftSeconds = 2.0;
    static constexpr double kHoldSeconds = 0.5;
    static constexpr double kRecenterSeconds = 2.0;
    static constexpr double kTotalSeconds = kShiftSeconds + kHoldSeconds + kRecenterSeconds;
    static constexpr double kGainRampSeconds = 0.5;
    static constexpr float kStandKp = 100.0f;
    static constexpr float kStandKd = 2.5f;
    static constexpr float kReducedKp = 60.0f;
    static constexpr float kReducedKd = 0.7f;

    explicit SupportedBodyShiftPlan(GainStrategy strategy) : strategy_(strategy), geometry_() {
        // Reuse the already-tested IK solution for the common 5 mm shift.
        // This body-only plan never samples the lift phases of that helper.
        stand_=geometry_.stand();
        shifted_=geometry_.shifted();
    }

    Sample At(double seconds) const {
        const double t=std::max(0.0,seconds);
        if(t<kShiftSeconds) return Interpolate(stand_,shifted_,t/kShiftSeconds,kShiftSeconds,Phase::ShiftWeight,t);
        if(t<kShiftSeconds+kHoldSeconds) return Hold(shifted_,Phase::HoldShift,t);
        if(t<kTotalSeconds) return Interpolate(shifted_,stand_,(t-kShiftSeconds-kHoldSeconds)/kRecenterSeconds,kRecenterSeconds,Phase::Recenter,t);
        auto result=Hold(stand_,Phase::Complete,t); result.complete=true; return result;
    }
    const std::array<Eigen::Vector3d,4>& stand() const { return stand_; }
    const std::array<Eigen::Vector3d,4>& shifted() const { return shifted_; }

private:
    using Pose=std::array<Eigen::Vector3d,4>;
    GainStrategy strategy_;
    SupportedLegLiftPlan geometry_;
    Pose stand_{},shifted_{};
    static double QuinticDerivative(double p) { const double s=std::clamp(p,0.0,1.0); return 30.0*s*s*(1.0-s)*(1.0-s); }
    std::pair<float,float> Gains(double elapsed) const {
        if(strategy_==GainStrategy::KeepStand) return {kStandKp,kStandKd};
        if(strategy_==GainStrategy::AbruptReduced) return {kReducedKp,kReducedKd};
        const double a=lite3::Quintic(std::clamp(elapsed/kGainRampSeconds,0.0,1.0));
        return {static_cast<float>(kStandKp+a*(kReducedKp-kStandKp)), static_cast<float>(kStandKd+a*(kReducedKd-kStandKd))};
    }
    Sample Interpolate(const Pose& from,const Pose& to,double p,double duration,Phase phase,double elapsed) const {
        const double blend=lite3::Quintic(p), rate=QuinticDerivative(p)/duration;
        const auto [kp,kd]=Gains(elapsed); Sample out; out.phase=phase;
        for(int leg=0;leg<4;++leg) for(int joint=0;joint<3;++joint) {
            const int i=3*leg+joint;
            out.command(i,0)=kp; out.command(i,1)=static_cast<float>(from[leg][joint]+blend*(to[leg][joint]-from[leg][joint]));
            out.command(i,2)=kd; out.command(i,3)=static_cast<float>(rate*(to[leg][joint]-from[leg][joint])); out.command(i,4)=0.0f;
        }
        return out;
    }
    Sample Hold(const Pose& pose,Phase phase,double elapsed) const { return Interpolate(pose,pose,0.0,1.0,phase,elapsed); }
};
