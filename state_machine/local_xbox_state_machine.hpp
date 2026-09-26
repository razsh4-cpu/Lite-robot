#pragma once

#include "state_base.h"
#include "local_xbox_control_permit.hpp"

#include <atomic>
#include <chrono>
#include <csignal>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <thread>

// Production state runner dedicated to a locally attached Xbox controller.
// It deliberately does not share the validation-console StateMachine API.
class LocalXboxStateMachine {
public:
    LocalXboxStateMachine(std::shared_ptr<RobotInterface> robot,
                          std::shared_ptr<UserCommandInterface> input,
                          std::shared_ptr<StateBase> idle,
                          std::shared_ptr<StateBase> stand,
                          std::shared_ptr<StateBase> rl,
                          std::shared_ptr<StateBase> damping)
        : current_(std::move(idle)), idle_(current_), stand_(std::move(stand)),
          rl_(std::move(rl)), damping_(std::move(damping)),
          input_(std::move(input)), robot_(std::move(robot)) {
        if(!robot_ || !input_ || !idle_ || !stand_ || !rl_ || !damping_)
            throw std::invalid_argument("local Xbox runtime dependencies");
        robot_->Start();
        input_->Start();
        current_->OnEnter();
    }

    ~LocalXboxStateMachine() {
        try { Shutdown(); } catch(...) {}
    }

    StateName CurrentState() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return current_name_;
    }

    bool ProcessOnce() {
        std::lock_guard<std::mutex> lock(mutex_);
        if(shutdown_complete_) return false;

        if(!robot_->IsFeedbackFresh()) {
            if(robot_->IsControlRequestSent()) ShutdownLocked();
            return !shutdown_complete_;
        }

        const bool input_connected=input_->IsConnected();
        if(!input_connected && current_name_==StateName::kIdle) {
            ShutdownLocked();
            return false;
        }

        const double stamp=robot_->GetInterfaceTimeStamp();
        if(stamp==last_stamp_) return true;
        last_stamp_=stamp;
        current_->Run();

        StateName next;
        if(!input_connected && current_name_!=StateName::kJointDamping)
            next=StateName::kJointDamping;
        else
            next=current_->LoseControlJudge()
                ? StateName::kJointDamping : current_->GetNextStateName();
        if(next==current_name_) return true;

        if(!ValidTransition(current_name_,next)) {
            ShutdownLocked();
            return false;
        }

        if(current_name_==StateName::kIdle && next==StateName::kStandUp) {
            // LB has already been edge-validated by XboxGamepadInterface and
            // IdleState has validated the measured robot state. Ownership is
            // intentionally not requested before this point.
            if(!robot_->AcquireControl()) return true;
            permit_=std::shared_ptr<const LocalXboxControlPermit>(
                new LocalXboxControlPermit(cancelled_));
            if(!robot_->OpenLocalXboxControl(permit_)) {
                cancelled_->store(true);
                permit_.reset();
                robot_->ReleaseControl();
                cancelled_=std::make_shared<std::atomic<bool>>(false);
                return true;
            }
        }

        current_->OnExit();
        current_=StateFor(next);
        current_name_=next;
        current_->OnEnter();

        if(next==StateName::kIdle) {
            cancelled_->store(true);
            robot_->SetJointCommandEnabled(false);
            permit_.reset();
            robot_->ReleaseControl();
            cancelled_=std::make_shared<std::atomic<bool>>(false);
            if(!input_connected) {
                ShutdownLocked();
                return false;
            }
        }
        return true;
    }

    void Run(const volatile std::sig_atomic_t* stop_signal=nullptr) {
        try {
            while(!stop_signal || *stop_signal==0) {
                if(!ProcessOnce()) break;
                std::this_thread::sleep_for(std::chrono::microseconds(500));
            }
        } catch(...) {
            Shutdown();
            throw;
        }
        Shutdown();
    }

    void Shutdown() {
        std::lock_guard<std::mutex> lock(mutex_);
        ShutdownLocked();
    }

private:
    static bool ValidTransition(StateName from, StateName to) {
        return (from==StateName::kIdle && to==StateName::kStandUp) ||
               (from==StateName::kStandUp && (to==StateName::kRLControl || to==StateName::kJointDamping)) ||
               (from==StateName::kRLControl && to==StateName::kJointDamping) ||
               (from==StateName::kJointDamping && to==StateName::kIdle);
    }

    std::shared_ptr<StateBase> StateFor(StateName name) const {
        switch(name) {
            case StateName::kIdle: return idle_;
            case StateName::kStandUp: return stand_;
            case StateName::kRLControl: return rl_;
            case StateName::kJointDamping: return damping_;
            default: throw std::runtime_error("invalid local Xbox state");
        }
    }

    void ShutdownLocked() {
        if(shutdown_complete_) return;
        // Invalidate first so an in-flight policy worker cannot send again.
        cancelled_->store(true);
        robot_->SetJointCommandEnabled(false);
        current_->OnExit();
        input_->Stop();
        permit_.reset();
        robot_->ReleaseControl();
        robot_->Stop();
        shutdown_complete_=true;
    }

    std::shared_ptr<StateBase> current_,idle_,stand_,rl_,damping_;
    std::shared_ptr<UserCommandInterface> input_;
    std::shared_ptr<RobotInterface> robot_;
    StateName current_name_{StateName::kIdle};
    double last_stamp_{-1.0};
    std::shared_ptr<std::atomic<bool>> cancelled_{
        std::make_shared<std::atomic<bool>>(false)};
    std::shared_ptr<const LocalXboxControlPermit> permit_;
    bool shutdown_complete_{false};
    mutable std::mutex mutex_;
};
