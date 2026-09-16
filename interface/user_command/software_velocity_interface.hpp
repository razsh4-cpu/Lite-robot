/**
 * Controller-free, policy-level velocity source.
 * This class never creates a socket or MotionSDK object; it only supplies the
 * existing UserCommand consumed by the state machine.
 */
#pragma once

#include "user_command_interface.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <mutex>

class SoftwareVelocityInterface final : public interface::UserCommandInterface {
public:
    explicit SoftwareVelocityInterface(
        std::chrono::milliseconds timeout = std::chrono::milliseconds(300))
        : timeout_(timeout) {
        std::memset(&usr_cmd_, 0, sizeof(usr_cmd_));
        last_velocity_command_ = Clock::now();
    }

    void Start() override {
        std::lock_guard<std::mutex> lock(mutex_);
        running_ = true;
        supervised_forward_=false;
        ZeroVelocityLocked();
        usr_cmd_.target_mode = msfb_.current_state;
    }

    void Stop() override {
        std::lock_guard<std::mutex> lock(mutex_);
        running_ = false;
        supervised_forward_=false;
        ZeroVelocityLocked();
        usr_cmd_.target_mode = msfb_.current_state;
    }

    UserCommand GetUserCommand() override {
        std::lock_guard<std::mutex> lock(mutex_);
        ApplySafetyGateLocked();
        return usr_cmd_;
    }

    void SetMotionStateFeedback(const MotionStateFeedback& msfb) override {
        std::lock_guard<std::mutex> lock(mutex_);
        msfb_ = msfb;
        if (msfb_.current_state != RobotMotionState::RLControlMode) {
            ZeroVelocityLocked();
        }
    }

    bool request_stand() {
        std::lock_guard<std::mutex> lock(mutex_);
        ZeroVelocityLocked();
        if (running_ && msfb_.current_state == RobotMotionState::WaitingForStand) {
            usr_cmd_.target_mode = RobotMotionState::StandingUp;
            return true;
        }
        return false;
    }

    bool request_rl_control() {
        std::lock_guard<std::mutex> lock(mutex_);
        ZeroVelocityLocked();
        if (running_ && msfb_.current_state == RobotMotionState::StandingUp) {
            usr_cmd_.target_mode = RobotMotionState::RLControlMode;
            return true;
        }
        return false;
    }

    void set_velocity_normalized(float forward, float lateral, float yaw) {
        std::lock_guard<std::mutex> lock(mutex_);
        if (zero_only_ || !running_ || msfb_.current_state != RobotMotionState::RLControlMode ||
            !std::isfinite(forward) || !std::isfinite(lateral) || !std::isfinite(yaw)) {
            ZeroVelocityLocked();
            return;
        }
        usr_cmd_.forward_vel_scale = Clamp(forward);
        usr_cmd_.side_vel_scale = Clamp(lateral);
        usr_cmd_.turnning_vel_scale = Clamp(yaw);
        last_velocity_command_ = Clock::now();
        has_velocity_command_ = true;
    }

    void stop() {
        std::lock_guard<std::mutex> lock(mutex_);
        ZeroVelocityLocked();
        usr_cmd_.target_mode = msfb_.current_state; // cancel queued stand/RL
    }

    UserCommand VelocitySnapshot() {
        std::lock_guard<std::mutex> lock(mutex_);
        ApplySafetyGateLocked();
        return usr_cmd_;
    }

private:
    friend class StateMachine;
    // One-way for this interface lifetime: no API can unlock a supervised zero test.
    void LockZeroOnly() {
        std::lock_guard<std::mutex> lock(mutex_);
        zero_only_=true; supervised_forward_=false; ZeroVelocityLocked();
    }
    void LockForwardTest() {
        std::lock_guard<std::mutex> lock(mutex_);
        zero_only_=true; supervised_forward_=true; ZeroVelocityLocked();
    }
    bool SetSupervisedForward(float forward) {
        std::lock_guard<std::mutex> lock(mutex_);
        if(!running_ || !zero_only_ || !supervised_forward_ ||
           msfb_.current_state!=RobotMotionState::RLControlMode ||
           !std::isfinite(forward) || forward<0 || forward>0.25f) {
            ZeroVelocityLocked();return false;
        }
        usr_cmd_.forward_vel_scale=forward;
        usr_cmd_.side_vel_scale=usr_cmd_.turnning_vel_scale=0;
        last_velocity_command_=Clock::now();has_velocity_command_=true;
        return true;
    }
    using Clock = std::chrono::steady_clock;

    static float Clamp(float value) {
        return std::max(-1.0f, std::min(1.0f, value));
    }

    void ZeroVelocityLocked() {
        usr_cmd_.forward_vel_scale = 0.0f;
        usr_cmd_.side_vel_scale = 0.0f;
        usr_cmd_.turnning_vel_scale = 0.0f;
        has_velocity_command_ = false;
        last_velocity_command_ = Clock::now();
    }

    void ApplySafetyGateLocked() {
        if ((zero_only_ && !supervised_forward_) || !running_ ||
            msfb_.current_state != RobotMotionState::RLControlMode ||
            !has_velocity_command_ || Clock::now() - last_velocity_command_ > timeout_) {
            ZeroVelocityLocked();
        } else if(supervised_forward_ &&
                  (usr_cmd_.forward_vel_scale<0 || usr_cmd_.forward_vel_scale>0.25f ||
                   usr_cmd_.side_vel_scale!=0 || usr_cmd_.turnning_vel_scale!=0)) {
            ZeroVelocityLocked();
        }
    }

    std::mutex mutex_;
    UserCommand usr_cmd_{};
    MotionStateFeedback msfb_{};
    std::chrono::milliseconds timeout_;
    Clock::time_point last_velocity_command_;
    bool running_{false};
    bool zero_only_{false};
    bool supervised_forward_{false};
    bool has_velocity_command_{false};
};
