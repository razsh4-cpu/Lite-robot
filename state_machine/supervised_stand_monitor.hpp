#pragma once
// Supported stand-test monitor. Limits are engineering guardrails, NOT vendor guarantees.
#include <array>
#include <cmath>
#include <limits>
#include <algorithm>
#include <deque>
#include "stand_diagnostics.hpp"

namespace supervised_stand {
struct Sample {
    std::array<double,12> position{}, velocity{}, target{}, target_velocity{};
    double roll=0, pitch=0;
    bool fresh=false, target_valid=false, final_target=false, new_feedback=true;
};
enum class Result { StandingUp, TargetReached, Abort };
class Monitor {
    double start_=0, last_=0, dwell_start_=0, reached_=0;
    bool active_=false, dwelling_=false, reached_target_=false;
    bool velocity_loss_pending_=false;
    double velocity_loss_start_=0;
    double dwell_roll_=0, dwell_pitch_=0;
    const char* reason_="not started";
    stand_diagnostics::MonitorStatus diagnostics_;
    struct SpeedPoint { double time; std::array<double,12> q, dq; };
    std::deque<SpeedPoint> speed_points_;
    // Operator-approved convergence-only change: 50 ms time-weighted RMS
    // velocity AND position range / 50 ms. Squaring prevents cancellation of
    // oscillatory velocity. Raw finite/position tracking/tilt guards are unchanged.
    bool SpeedSettled(double now, const Sample& s) {
        if(!s.new_feedback) {
            return diagnostics_.speed_window_ready && !speed_points_.empty() &&
                now-speed_points_.back().time<=speed_window &&
                diagnostics_.rms_max_speed<=max_converged_speed &&
                diagnostics_.position_range_speed<=max_converged_speed;
        }
        // Repeated wall timestamps cannot supply an additional timed sample.
        if(!speed_points_.empty() && now<=speed_points_.back().time) return false;
        if(!speed_points_.empty() && now-speed_points_.back().time>speed_window)
            speed_points_.clear(); // never fill a gap by interpolation
        speed_points_.push_back({now,s.position,s.velocity});
        const double cutoff=now-speed_window;
        while(speed_points_.size()>1 && speed_points_[1].time<=cutoff)
            speed_points_.pop_front();
        if(speed_points_.size()>512) speed_points_.clear(); // bounded; fails closed
        diagnostics_.speed_window_ready=speed_points_.size()>1 &&
            speed_points_.front().time<=cutoff+1e-9;
        diagnostics_.rms_max_speed=diagnostics_.position_range_speed=0;
        if(!diagnostics_.speed_window_ready) return false;
        for(unsigned j=0;j<12;++j) {
            double integral=0, lo=s.position[j], hi=lo;
            for(size_t k=0;k<speed_points_.size();++k) {
                const auto& p=speed_points_[k];
                // Including the boundary sample slightly before the window is
                // conservative for position range; it cannot hide movement.
                lo=std::min(lo,p.q[j]); hi=std::max(hi,p.q[j]);
                if(k==0) continue;
                const auto& a=speed_points_[k-1];
                const double begin=std::max(a.time,cutoff), dt=p.time-begin;
                if(dt<=0) continue;
                const double a2=a.dq[j]*a.dq[j], b2=p.dq[j]*p.dq[j];
                if(!std::isfinite(a2) || !std::isfinite(b2)) {
                    diagnostics_.rms_max_speed=std::numeric_limits<double>::infinity();
                    return false;
                }
                const double clipped=a2+(b2-a2)*(begin-a.time)/(p.time-a.time);
                integral+=.5*(clipped+b2)*dt;
            }
            diagnostics_.rms_max_speed=std::max(diagnostics_.rms_max_speed,
                std::sqrt(std::max(0.,integral)/speed_window));
            diagnostics_.position_range_speed=std::max(diagnostics_.position_range_speed,
                (hi-lo)/speed_window);
        }
        return diagnostics_.rms_max_speed<=max_converged_speed &&
               diagnostics_.position_range_speed<=max_converged_speed;
    }
public:
    // All time inputs are monotonic wall-clock seconds, NOT robot timestamps.
    static constexpr double deadline=6.0, dwell=0.5;
    static constexpr double max_tracking=0.35, convergence=0.08;
    static constexpr double max_converged_speed=0.15, max_tilt=0.35;
    static constexpr double speed_window=0.05;
    // Once standing is established, require the RMS-only violation to survive
    // two complete speed windows. A short estimator burst remains represented
    // by the first 50 ms RMS window after the raw motion has ended; using only
    // one window as the persistence timer can therefore turn that isolated
    // burst into a false persistent-loss abort. The 0.15 rad/s limit is
    // unchanged. Position motion and every other guard still fail immediately.
    static constexpr double hold_velocity_loss_persistence=2*speed_window;
    const char* reason() const { return reason_; }
    stand_diagnostics::MonitorStatus diagnostics() const {
        auto result=diagnostics_;
        result.wall=last_; result.elapsed=last_-start_;
        result.dwell_elapsed=dwelling_?last_-dwell_start_:0;
        result.observation_elapsed=reached_target_?last_-reached_:0;
        result.reason=reason_;
        return result;
    }
    void Start(double now) {
        active_=std::isfinite(now); start_=last_=now;
        dwelling_=reached_target_=velocity_loss_pending_=false; reason_="standing up";
        diagnostics_={};
        speed_points_.clear();
    }
    Result Abort(const char* reason) { active_=false; reason_=reason; return Result::Abort; }
    Result Check(double now, const Sample& s, bool abort_requested=false) {
        if(!active_) return Result::Abort;
        if(abort_requested) return Abort("operator/signal abort");
        if(!std::isfinite(now) || now<last_) return Abort("invalid wall clock");
        last_=now;
        diagnostics_.final_target=s.final_target;
        diagnostics_.new_feedback=s.new_feedback;
        diagnostics_.candidate=false; diagnostics_.raw_max_speed=0;
        if(!s.fresh) return Abort("stale telemetry");
        if(!std::isfinite(s.roll) || !std::isfinite(s.pitch)) return Abort("invalid IMU");
        if(std::abs(s.roll)>max_tilt || std::abs(s.pitch)>max_tilt) return Abort("tilt limit");
        bool converged=s.target_valid && s.final_target;
        for(unsigned i=0;i<12;++i) {
            diagnostics_.raw_max_speed=std::max(diagnostics_.raw_max_speed,std::abs(s.velocity[i]));
            if(!std::isfinite(s.position[i]) || !std::isfinite(s.velocity[i]))
                return Abort("invalid measured joints");
            if(!s.target_valid) continue;
            if(!std::isfinite(s.target[i]) || !std::isfinite(s.target_velocity[i]))
                return Abort("invalid target");
            const auto error=std::abs(s.position[i]-s.target[i]);
            if(error>max_tracking) return Abort("tracking error");
            if(error>convergence ||
                std::abs(s.target_velocity[i])>0.001) converged=false;
        }
        const bool posture_converged=converged;
        const bool speed_settled=SpeedSettled(now,s);
        if(!speed_settled) converged=false;
        const bool attitude_settled=!dwelling_ ||
            (std::abs(s.roll-dwell_roll_)<=0.03 && std::abs(s.pitch-dwell_pitch_)<=0.03);
        if(!attitude_settled) converged=false;
        diagnostics_.candidate=converged;
        if(reached_target_ && !converged) {
            const bool rms_only=posture_converged && attitude_settled &&
                diagnostics_.speed_window_ready &&
                std::isfinite(diagnostics_.rms_max_speed) &&
                diagnostics_.position_range_speed<=max_converged_speed &&
                diagnostics_.rms_max_speed>max_converged_speed;
            if(!rms_only) return Abort("lost convergence");
            if(s.new_feedback) {
                if(!velocity_loss_pending_) {velocity_loss_pending_=true;velocity_loss_start_=now;}
                else if(now-velocity_loss_start_>=hold_velocity_loss_persistence)
                    return Abort("persistent velocity convergence loss");
            }
            return Result::TargetReached;
        }
        if(reached_target_) velocity_loss_pending_=false;
        // Successful supported stand holds until an operator stop/release or
        // a failed guard. Elapsed time after success alone is not an abort.
        if(!reached_target_ && now-start_>=deadline) return Abort("convergence deadline");
        if(!s.new_feedback) return reached_target_ ? Result::TargetReached : Result::StandingUp;
        if(!converged) dwelling_=false;
        else if(!dwelling_) { dwelling_=true; dwell_start_=now; dwell_roll_=s.roll; dwell_pitch_=s.pitch; }
        else if(!reached_target_ && now-dwell_start_>=dwell) {
            reached_target_=true; reached_=now; reason_="target reached";
        }
        return reached_target_ ? Result::TargetReached : Result::StandingUp;
    }
};
}
