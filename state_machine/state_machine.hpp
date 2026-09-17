/**
 * @file state_machine.hpp
 * @brief for robot to switch control state by user command input
 * @author mazunwang
 * @version 1.0
 * @date 2024-05-29
 * 
 * @copyright Copyright (c) 2024  DeepRobotics
 * 
 */
#pragma once

#include "state_base.h"
#include "idle_state.hpp"
#include "standup_state.hpp"
#include "joint_damping_state.hpp"

// #ifdef USE_ONNX
//     #include "rl_control_state_onnx.hpp"
// #else   
//     #include "rl_control_state.hpp"
// #endif

#include "rl_control_state_onnx.hpp"

#ifdef BUILD_SIMULATION
#include "keyboard_interface.hpp"
#include "xbox_gamepad_interface.hpp"
#endif
#include "software_velocity_interface.hpp"
#include "supervised_stand_monitor.hpp"
#include <atomic>
#include <functional>
#include <fcntl.h>
#include <unistd.h>
#include <csignal>
#include <mutex>
#ifdef USE_RAISIM
    #include "simulation/jueying_raisim_simulation.hpp"
#endif
#ifdef USE_PYBULLET
    #include "simulation/simulation_interface.hpp"
#endif

#ifdef USE_MJCPP
    #include "simulation/mujoco_interface.hpp"
#endif

#include "hardware/hardware_interface.hpp"
#include "data_streaming.hpp"

class StateMachine{
private:
    std::shared_ptr<StateBase> current_controller_;
    std::shared_ptr<StateBase> idle_controller_;
    std::shared_ptr<StateBase> standup_controller_;
    std::shared_ptr<StandUpState> typed_standup_controller_;
    std::shared_ptr<StateBase> rl_controller_;
    std::shared_ptr<StateBase> joint_damping_controller_;

    StateName current_state_name_, next_state_name_;

    std::shared_ptr<UserCommandInterface> uc_ptr_;
    std::shared_ptr<SoftwareVelocityInterface> software_velocity_interface_;
    std::shared_ptr<RobotInterface> ri_ptr_;
    std::shared_ptr<ControlParameters> cp_ptr_;

    std::shared_ptr<DataStreaming> ds_ptr_;
    bool shutdown_complete_{false};
    mutable std::mutex lifecycle_mutex_;
    double time_record_{-1.0};
    const std::shared_ptr<std::atomic<bool>> abort_requested_ = std::make_shared<std::atomic<bool>>(false);
    std::atomic<bool> shutdown_intent_{false};
    const std::atomic<bool>* shutdown_signal_{nullptr};
    std::function<double()> stand_now_ = [] {
        return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();
    };
    supervised_stand::Monitor stand_monitor_;
    bool stand_armed_{false}, stand_pending_{false}, stand_active_{false}, have_stand_command_{false};
    bool release_attempted_{false};
    uint64_t acquisition_epoch_{0}, used_epoch_{0};
    double arm_deadline_{0}, stand_robot_start_{0}, last_command_stamp_{0};
    double target_reached_started_{-1.0};
    bool supported_leg_test_requested_{false};
    bool supported_leg_test_active_{false};
    bool supported_leg_test_finishing_{false};
    bool supported_leg_test_have_command_{false};
    double supported_leg_test_started_{0.0};
    std::string stand_status_{"LOCKED"}, abort_reason_;
    std::string stand_preflight_reason_{"not checked"};
    std::shared_ptr<const StandOnlyPermit> stand_permit_;
    std::shared_ptr<const RLZeroPermit> rl_zero_permit_;
    bool rl_zero_active_{false};
    bool rl_forward_active_{false}, forward_test_used_{false}, forward_pulse_seen_{false};
    double rl_zero_started_{0};
    double rl_forward_started_{0};
    std::shared_ptr<const RLForwardPermit> rl_forward_permit_;

    bool AbortRequested() const {
        return abort_requested_->load() || shutdown_intent_.load() ||
            (shutdown_signal_ && shutdown_signal_->load());
    }
    void StandStatus(const char* status) {
        if(stand_status_!=status) { stand_status_=status; std::cout<<"STAND_TEST "<<status<<std::endl; }
    }
    supervised_stand::Sample StandSample(bool new_feedback) {
        supervised_stand::Sample sample;
        const auto feedback=ri_ptr_->GetStandFeedback();
        sample.fresh=feedback.fresh; sample.new_feedback=new_feedback;
        const auto& q=feedback.q; const auto& dq=feedback.dq;
        const auto& rpy=feedback.rpy;
        if(q.size()!=12 || dq.size()!=12 || !q.allFinite() || !dq.allFinite() || !rpy.allFinite()) {
            sample.fresh=false; return sample;
        }
        for(int i=0;i<12;++i) { sample.position[i]=q[i]; sample.velocity[i]=dq[i]; }
        sample.roll=rpy[0]; sample.pitch=rpy[1];
        sample.target_valid=have_stand_command_;
        if(have_stand_command_) {
            const auto command=ri_ptr_->GetJointCommand();
            if(command.rows()!=12 || command.cols()!=5 || !command.allFinite()) {
                sample.fresh=false; return sample;
            }
            for(int i=0;i<12;++i) { sample.target[i]=command(i,1); sample.target_velocity[i]=command(i,3); }
            const double duration=cp_ptr_ ? 2.0*cp_ptr_->stand_duration_ : 3.0;
            sample.final_target=supported_leg_test_finishing_ ||
                last_command_stamp_-stand_robot_start_>=duration;
        }
        return sample;
    }
    bool StandPreflight() {
        auto sample=StandSample(false);
        stand_preflight_reason_="OK";
        if(!sample.fresh) {stand_preflight_reason_="stale or invalid feedback";return false;}
        if(std::abs(sample.roll)>supervised_stand::Monitor::max_tilt ||
           std::abs(sample.pitch)>supervised_stand::Monitor::max_tilt) {stand_preflight_reason_="tilt limit";return false;}
        for(int i=0;i<12;++i) {
            if(std::abs(sample.velocity[i])>0.15) {stand_preflight_reason_="joint "+std::to_string(i)+" not stationary";return false;}
            if(cp_ptr_) {
                // Match the existing IdleState limits/tolerance, NOT new calibrated limits.
                double lower=cp_ptr_->fl_joint_lower_[i%3]-.1, upper=cp_ptr_->fl_joint_upper_[i%3]+.1;
                if(i%3==0 && (i/3)%2==1) {const auto old=lower;lower=-upper;upper=-old;}
                if(sample.position[i]<lower || sample.position[i]>upper) {
                    stand_preflight_reason_="joint "+std::to_string(i)+" "+stand_diagnostics::Leg(i)+" "+
                        stand_diagnostics::Joint(i)+" q="+std::to_string(sample.position[i])+" outside ["+
                        std::to_string(lower)+","+std::to_string(upper)+"]";
                    return false;
                }
            }
        }
        const auto cmd=software_velocity_interface_->VelocitySnapshot();
        if(cmd.forward_vel_scale!=0 || cmd.side_vel_scale!=0 || cmd.turnning_vel_scale!=0) {
            stand_preflight_reason_="nonzero software velocity";return false;
        }
        return true;
    }
    // Shared abort: gate closure is serialized with SendCmd; no posture/hold packets.
    // Mechanical support is mandatory because vendor release may remove stiffness.
    void AbortStandLocked(const char* reason) {
        abort_requested_->store(true);
        if(ri_ptr_ && (stand_active_ || stand_pending_ || rl_zero_active_ || rl_forward_active_)) {
            try { ri_ptr_->RecordStandEvent(2,reason); } catch(...) {}
        }
        stand_armed_=stand_pending_=stand_active_=false;
        supported_leg_test_requested_=supported_leg_test_active_=
            supported_leg_test_finishing_=supported_leg_test_have_command_=false;
        target_reached_started_=-1.0;
        rl_zero_active_=rl_forward_active_=false; rl_zero_permit_.reset();rl_forward_permit_.reset();
        stand_permit_.reset();
        if(ri_ptr_) ri_ptr_->SetJointCommandEnabled(false);
        // The first abort below stops then deliberately restarts the passive
        // operator input after returning to Idle. Later worker ticks must be a
        // true no-op: stopping it again made the next acquire able to arm but
        // unable to submit its stand request.
        if(release_attempted_) return; // never retry release or disturb reset Idle input
        if(uc_ptr_) uc_ptr_->Stop();
        StandStatus("ABORTING"); abort_reason_=reason;
        if(current_controller_) current_controller_->OnExit(); // join before ownership release
        current_controller_=idle_controller_;
        current_state_name_=next_state_name_=kIdle;
        release_attempted_=true;
        if(ri_ptr_ && ri_ptr_->IsControlRequestSent()) {
            try { ri_ptr_->ReleaseControl(); }
            catch(...) {
                abort_reason_+="; release failed, ownership unconfirmed";
                try { ri_ptr_->FinishStandDiagnostics(abort_reason_); } catch(...) {}
                throw;
            }
            StandStatus("RELEASE_REQUESTED");
        } else StandStatus("LOCKED");
        if(current_controller_) current_controller_->OnEnter();
        if(uc_ptr_) uc_ptr_->Start();
        have_stand_command_=false; time_record_=-1.0;
        // Logging must never delay closing the gate or requesting release.
        if(ri_ptr_) { try { ri_ptr_->FinishStandDiagnostics(abort_reason_); } catch(...) {
            std::cerr<<"STAND_TRACE write failed after release"<<std::endl;
        } }
    }

    void ReleaseLocked() { AbortStandLocked("release requested"); }
    void ShutdownLocked() {
        if(shutdown_complete_) return;
        shutdown_intent_.store(true);
        AbortStandLocked("shutdown/signal");
        shutdown_complete_=true;
    }

    void GetDataStreaming(){
        if(!ri_ptr_) return;
        VecXf pos = ri_ptr_->GetJointPosition();
        VecXf vel = ri_ptr_->GetJointVelocity();
        VecXf tau = ri_ptr_->GetJointTorque();
        Vec3f rpy = ri_ptr_->GetImuRpy();
        Vec3f acc = ri_ptr_->GetImuAcc();
        Vec3f omg = ri_ptr_->GetImuOmega();
        MatXf jc = ri_ptr_->GetJointCommand();

        ds_ptr_->InsertInterfaceTime(ri_ptr_->GetInterfaceTimeStamp());
        ds_ptr_->InsertJointData("q", pos);
        ds_ptr_->InsertJointData("dq", vel);
        ds_ptr_->InsertJointData("tau", tau);
        ds_ptr_->InsertJointData("q_cmd", jc.col(1));
        ds_ptr_->InsertJointData("tau_ff", jc.col(4));

        ds_ptr_->InsertImuData("rpy", rpy);
        ds_ptr_->InsertImuData("acc", acc);
        ds_ptr_->InsertImuData("omg", omg);

        if(!uc_ptr_) return;
        auto cmd = uc_ptr_->GetUserCommand();
        ds_ptr_->InsertCommandData("target_mode", float(cmd.target_mode));

        ds_ptr_->InsertStateData("current_state", StateBase::msfb_.current_state);
       
        ds_ptr_->SendData();
    }

    std::shared_ptr<StateBase> GetNextStatePtr(StateName state_name){
        switch(state_name){
            case StateName::kInvalid:{
                return nullptr;
            }
            case StateName::kIdle:{
                return idle_controller_;
            }
            case StateName::kStandUp:{
                return standup_controller_;
            }
            case StateName::kRLControl:{
                return rl_controller_;
            }
            case StateName::kJointDamping:{
                return joint_damping_controller_;
            }
            default:{
                std::cerr << "error state name" << std::endl;
            }
        }
        return nullptr;
    }
    const char* SupportedLegPhaseStatus() const {
        if(!typed_standup_controller_) return "LEG_TEST_INVALID";
        using P=SupportedLegLiftPlan::Phase;
        switch(typed_standup_controller_->SupportedLegLiftPhase()) {
            case P::ShiftBody: return "LEG_TEST_SHIFT_BODY";
            case P::HoldShift: return "LEG_TEST_HOLD_SHIFT";
            case P::LiftFrontRight: return "LEG_TEST_LIFT_FR";
            case P::HoldFrontRight: return "LEG_TEST_HOLD_FR";
            case P::LowerFrontRight: return "LEG_TEST_LOWER_FR";
            case P::RecenterBody: return "LEG_TEST_RECENTER";
            case P::Complete: return "LEG_TEST_VERIFY_STAND";
        }
        return "LEG_TEST_INVALID";
    }
    bool SupportedLegTestGuard() {
        if(!supported_leg_test_active_ || !typed_standup_controller_ ||
           current_controller_!=standup_controller_ || current_state_name_!=kStandUp ||
           !ri_ptr_->IsControlRequestSent() || !ri_ptr_->JointCommandsEnabled() ||
           !stand_permit_ || !stand_permit_->Valid() ||
           stand_now_()-supported_leg_test_started_>SupportedLegLiftPlan::kTotalSeconds+0.75)
            return false;
        const auto s=ri_ptr_->GetStandFeedback();
        if(!s.valid || !s.fresh || s.q.size()!=12 || s.dq.size()!=12 ||
           !s.q.allFinite() || !s.dq.allFinite() || !s.rpy.allFinite() ||
           std::abs(s.rpy[0])>3.0*M_PI/180.0 || std::abs(s.rpy[1])>3.0*M_PI/180.0 ||
           s.dq.cwiseAbs().maxCoeff()>0.50) return false;
        if(!supported_leg_test_have_command_) return true;
        const auto command=ri_ptr_->GetJointCommand();
        return typed_standup_controller_->SupportedLegLiftCommandWithinBounds(command) &&
            (command.col(1)-s.q).cwiseAbs().maxCoeff()<=0.15;
    }
public:
    StateMachine(RobotType robot_type){
        const std::string activation_key = "~/raisim/activation.raisim";
        std::string urdf_path = "";
        std::string mjcf_path = "";
        #ifdef BUILD_SIMULATION
            // 检测Xbox手柄是否存在
            std::string js_device = "/dev/input/js0";
            int js_fd = open(js_device.c_str(), O_RDONLY);
            if(js_fd >= 0){
                close(js_fd);
                std::cout << "Xbox gamepad detected, using XboxGamepadInterface" << std::endl;
                uc_ptr_ = std::make_shared<XboxGamepadInterface>(js_device);
            } else {
                std::cout << "No Xbox gamepad detected, using KeyboardInterface" << std::endl;
                uc_ptr_ = std::make_shared<KeyboardInterface>();
            }
        #else
            // Real hardware uses an application-provided velocity source.
            // Retroid/Xbox implementations remain available but are not required.
            software_velocity_interface_ = std::make_shared<SoftwareVelocityInterface>();
            uc_ptr_ = software_velocity_interface_;
        #endif
        // uc_ptr_ = std::make_shared<KeyboardInterface>();
        // uc_ptr_ = std::make_shared<RetroidGamepadInterface>(12121);
        if(robot_type == RobotType::Lite3){
            urdf_path = GetAbsPath()+"/../third_party/URDF_model/lite3_urdf/Lite3/urdf/Lite3.urdf";
            mjcf_path = GetAbsPath()+"third_party/URDF_model/Lite3/Lite3_mjcf/mjcf/Lite3.xml";
            #ifdef USE_RAISIM
                ri_ptr_ = std::make_shared<JueyingRaisimSimulation>(activation_key, urdf_path, "Lite3_sim");

            #elif defined(USE_MJCPP)
                ri_ptr_ = std::make_shared<MujocoInterface>("Lite3", mjcf_path);
                std::cout << "Using MujocoInterface CPP " << std::endl;
                std::cout << "mjcf_path: " << mjcf_path << std::endl;
            #elif defined(USE_PYBULLET)
                ri_ptr_ = std::make_shared<SimulationInterface>("Lite3");
            #else
                ri_ptr_ = std::make_shared<HardwareInterface>("Lite3");
            #endif
            cp_ptr_ = std::make_shared<ControlParameters>(robot_type);
        }else{
            std::cerr << "error" << std::endl;
        }

        std::shared_ptr<ControllerData> data_ptr = std::make_shared<ControllerData>();
        data_ptr->ri_ptr = ri_ptr_;
        data_ptr->uc_ptr = uc_ptr_;
        data_ptr->cp_ptr = cp_ptr_;
        ds_ptr_ = std::make_shared<DataStreaming>(false, false);
        data_ptr->ds_ptr = ds_ptr_;

        idle_controller_ = std::make_shared<IdleState>(robot_type, "idle_state", data_ptr);
        standup_controller_ = std::make_shared<StandUpState>(robot_type, "standup_state", data_ptr);
        typed_standup_controller_ = std::static_pointer_cast<StandUpState>(standup_controller_);

        // 测试ONNX，后续需要改成参数控制
        // rl_controller_ = std::make_shared<RLControlState>(robot_type, "rl_control", data_ptr);
        // #ifdef USE_ONNX
        //     rl_controller_ = std::make_shared<RLControlStateONNX>(robot_type, "rl_control", data_ptr);
        // #else
        //     rl_controller_ = std::make_shared<RLControlState>(robot_type, "rl_control", data_ptr);
        // #endif
        rl_controller_ = std::make_shared<RLControlStateONNX>(robot_type, "rl_control", data_ptr);
        


        joint_damping_controller_ = std::make_shared<JointDampingState>(robot_type, "joint_damping", data_ptr);

        current_controller_ = idle_controller_;
        current_state_name_ = kIdle;
        next_state_name_ = kIdle;
   
        // std::cout << "Controller will be enabled in 3 seconds!!!" << std::endl;
        // std::this_thread::sleep_for(std::chrono::seconds(3)); //for safety 

        ri_ptr_->Start();
        std::cout << "Robot interface started" << std::endl;
        uc_ptr_->Start();
        
        current_controller_->OnEnter();  
    }

    // Injected dependencies for offline integration tests. No production SDK,
    // policy loader or socket is constructed by this overload.
    StateMachine(std::shared_ptr<RobotInterface> robot,
                 std::shared_ptr<SoftwareVelocityInterface> input,
                 std::shared_ptr<StateBase> idle, std::shared_ptr<StateBase> stand,
                 std::shared_ptr<StateBase> rl, std::shared_ptr<StateBase> damping,
                 std::function<double()> clock = {}, std::shared_ptr<ControlParameters> parameters = {})
        : current_controller_(idle), idle_controller_(idle), standup_controller_(stand),
          rl_controller_(rl), joint_damping_controller_(damping),
          current_state_name_(kIdle), next_state_name_(kIdle), uc_ptr_(input),
          software_velocity_interface_(input), ri_ptr_(robot) {
        if(clock) stand_now_=std::move(clock);
        typed_standup_controller_=std::dynamic_pointer_cast<StandUpState>(standup_controller_);
        cp_ptr_=std::move(parameters);
        ri_ptr_->Start();
        uc_ptr_->Start();
        current_controller_->OnEnter();
    }
    ~StateMachine() {
        try { Shutdown(); }
        catch (const std::exception& e) {
            std::cerr << "Shutdown failed; ownership return unconfirmed: " << e.what() << std::endl;
        }
    }

    bool AcquireHardwareControl() {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        if (shutdown_complete_ || shutdown_intent_.load() || !ri_ptr_ || !ri_ptr_->IsFeedbackFresh()) return false;
        if(ri_ptr_->IsControlRequestSent()) return !release_attempted_;
        if(!ri_ptr_->AcquireControl()) return false;
        ++acquisition_epoch_; release_attempted_=false;
        abort_requested_->store(false);
        target_reached_started_=-1.0;
        StandStatus("LOCKED"); abort_reason_.clear();
        return true;
    }
    void ReleaseHardwareControl() {
        abort_requested_->store(true);
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        if (!shutdown_complete_) ReleaseLocked();
    }
    bool IsHardwareControlAcquired() const {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        return ri_ptr_ && ri_ptr_->IsControlAcquired();
    }
    bool IsControlRequestSent() const {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        return ri_ptr_ && ri_ptr_->IsControlRequestSent();
    }
    const char* OwnershipStatus() const {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        return ri_ptr_ ? ri_ptr_->OwnershipStatus() : "NOT_REQUESTED";
    }
    bool TelemetryFresh() const {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        return ri_ptr_ && ri_ptr_->IsFeedbackFresh();
    }
    double TelemetryAgeSeconds() const {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        return ri_ptr_ ? ri_ptr_->FeedbackAgeSeconds() : std::numeric_limits<double>::infinity();
    }
    bool JointCommandsEnabled() const {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        return ri_ptr_ && ri_ptr_->JointCommandsEnabled();
    }
    int CurrentMotionState() const {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        return static_cast<int>(current_state_name_);
    }
    UserCommand VelocitySnapshot() {
        return software_velocity_interface_ ? software_velocity_interface_->VelocitySnapshot() : UserCommand{};
    }
    // Explicit operator attestations are not inferred from SDK telemetry.
    bool AuthorizeStandTest(bool mechanically_supported, bool estop_ready,
                            bool health_reviewed, bool limits_accepted) {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        return AuthorizeStandTestLocked(mechanically_supported, estop_ready, health_reviewed, limits_accepted);
    }
private:
    // Caller holds lifecycle_mutex_; shared by the separate and combined actions.
    bool AuthorizeStandTestLocked(bool mechanically_supported, bool estop_ready,
                                  bool health_reviewed, bool limits_accepted) {
        if(!mechanically_supported || !estop_ready || !health_reviewed || !limits_accepted ||
           shutdown_complete_ || AbortRequested() || !software_velocity_interface_ ||
           !ri_ptr_->IsControlRequestSent() || ri_ptr_->JointCommandsEnabled() ||
           current_state_name_!=kIdle || stand_armed_ || stand_pending_ || stand_active_ ||
           acquisition_epoch_==0 || used_epoch_==acquisition_epoch_ || !StandPreflight()) return false;
        used_epoch_=acquisition_epoch_; stand_armed_=true;
        arm_deadline_=stand_now_()+5.0; StandStatus("ARMED");
        return true; // no packet, no gate, no ownership claim
    }
public:
    bool RequestStandOnce(const std::string& acknowledgement) {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        if(acknowledgement!="SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED") return false;
        if(!AuthorizeStandTestLocked(true,true,true,true)) return false;
        // No worker iteration can interleave authorization and request. All
        // existing request checks run again; entry/send gates remain unchanged.
        return RequestStandLocked();
    }
    bool RequestSupportedLegLiftOnce(const std::string& acknowledgement) {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        if(acknowledgement!="SUPPORTED_ESTOP_LEG_TEST_LIMITS_CONFIRMED" ||
           !typed_standup_controller_) return false;
        if(!AuthorizeStandTestLocked(true,true,true,true)) return false;
        supported_leg_test_requested_=true;
        if(RequestStandLocked()) return true;
        supported_leg_test_requested_=false;
        return false;
    }
    std::string StandTestStatus() const {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_); return stand_status_;
    }
    std::string StandAbortReason() const {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_); return abort_reason_;
    }
    std::string StandPreflightReason() {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        StandPreflight(); return stand_preflight_reason_; // read-only, never arms/opens gate
    }
    bool RequestStand() {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        return RequestStandLocked();
    }
private:
    bool RequestStandLocked() {
        if(shutdown_complete_ || AbortRequested() || !stand_armed_ ||
           stand_now_()>=arm_deadline_ || !ri_ptr_->IsControlRequestSent() ||
           current_state_name_!=kIdle || !StandPreflight()) return false;
        if(!software_velocity_interface_->request_stand()) return false;
        stand_armed_=false; stand_pending_=true;
        StandStatus("PENDING");
        return true; // actual OnEnter MUST precede gate opening
    }
public:
    bool RequestRLControl() { return false; } // stand-only validation; never enable policy
    bool RequestRLZeroOnce(const std::string& acknowledgement) {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        if(acknowledgement!="SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED" || shutdown_complete_ ||
           AbortRequested() || rl_zero_active_ || !stand_active_ || stand_status_!="TARGET_REACHED" ||
           current_state_name_!=kStandUp || current_controller_!=standup_controller_ ||
           !ri_ptr_->IsControlRequestSent() || !ri_ptr_->JointCommandsEnabled() ||
           !stand_permit_ || !stand_permit_->Valid() || !StandPreflight()) return false;
        // Recheck the hold immediately; a cached TARGET_REACHED is insufficient.
        if(stand_monitor_.Check(stand_now_(),StandSample(false))!=supervised_stand::Result::TargetReached) {
            AbortStandLocked("RL zero entry hold check failed"); return false;
        }
        software_velocity_interface_->LockZeroOnly();
        try {
            ri_ptr_->SetJointCommandEnabled(false);
            current_controller_->OnExit();
            if(AbortRequested() || !StandPreflight()) {AbortStandLocked("RL zero entry preflight failed");return false;}
            if(!software_velocity_interface_->request_rl_control()) {AbortStandLocked("RL zero input transition rejected");return false;}
            stand_active_=false; stand_permit_.reset();
            current_controller_=rl_controller_; current_state_name_=next_state_name_=kRLControl;
            rl_zero_permit_=std::shared_ptr<const RLZeroPermit>(new RLZeroPermit(abort_requested_,shutdown_signal_));
            current_controller_->OnEnter(); // worker starts; gate CLOSED and no observation yet
            if(AbortRequested() || !StandPreflight() || !ri_ptr_->OpenSupervisedRLZero(rl_zero_permit_)) {
                AbortStandLocked("RL zero grant rejected");return false;
            }
            rl_zero_active_=true; rl_zero_started_=stand_now_();
            ri_ptr_->RecordStandEvent(1,"RL_ZERO_ACTIVE: 8s maximum, operator authorization, ownership unconfirmed");
            StandStatus("RL_ZERO_ACTIVE");
            return true; // next fresh state-machine tick supplies first policy observation
        } catch(...) {AbortStandLocked("RL zero entry exception");throw;}
    }
    bool RequestForwardOnce(const std::string& acknowledgement) {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        if(acknowledgement!="SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED" || forward_test_used_ ||
           shutdown_complete_ || AbortRequested() || rl_zero_active_ || rl_forward_active_ ||
           !stand_active_ || stand_status_!="TARGET_REACHED" || current_state_name_!=kStandUp ||
           current_controller_!=standup_controller_ || !ri_ptr_->IsControlRequestSent() ||
           !ri_ptr_->JointCommandsEnabled() || !stand_permit_ || !stand_permit_->Valid() ||
           !StandPreflight()) return false;
        if(stand_monitor_.Check(stand_now_(),StandSample(false))!=supervised_stand::Result::TargetReached) {
            AbortStandLocked("RL forward entry hold check failed");return false;
        }
        forward_test_used_=true;
        software_velocity_interface_->LockForwardTest();
        try {
            ri_ptr_->SetJointCommandEnabled(false);current_controller_->OnExit();
            if(AbortRequested() || !StandPreflight()) {AbortStandLocked("RL forward entry preflight failed");return false;}
            if(!software_velocity_interface_->request_rl_control()) {AbortStandLocked("RL forward input transition rejected");return false;}
            stand_active_=false;stand_permit_.reset();
            current_controller_=rl_controller_;current_state_name_=next_state_name_=kRLControl;
            rl_forward_permit_=std::shared_ptr<const RLForwardPermit>(new RLForwardPermit(abort_requested_,shutdown_signal_));
            current_controller_->OnEnter();
            if(AbortRequested() || !StandPreflight() || !ri_ptr_->OpenSupervisedRLForward(rl_forward_permit_)) {
                AbortStandLocked("RL forward grant rejected");return false;
            }
            rl_forward_active_=true;forward_pulse_seen_=false;rl_forward_started_=stand_now_();
            ri_ptr_->RecordStandEvent(1,"RL_FORWARD_ZERO_STABILIZING: pulse +0.25 after 1s for 1.00s");
            StandStatus("RL_FORWARD_ZERO_STABILIZING");
            return true;
        }catch(...){AbortStandLocked("RL forward entry exception");throw;}
    }
    void SetVelocityNormalized(float, float, float) {
        // A velocity request during this test is misuse, not a locomotion command.
        StopVelocity();
    }
    void StopVelocity() {
        abort_requested_->store(true); // visible before waiting for lifecycle mutex
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        AbortStandLocked("stop requested");
    }
    void Shutdown() {
        shutdown_intent_.store(true); abort_requested_->store(true);
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        ShutdownLocked();
    }
    // One serialized control iteration, also used by inert integration tests.
    bool ProcessOnce() {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        if(shutdown_complete_) return false;
        try {
            // Checked BEFORE timestamp skip, trajectory Run(), or any transition.
            if(AbortRequested()) { AbortStandLocked("stop/signal"); return true; }
            if(!ri_ptr_->IsFeedbackFresh()) {
                // Receiver startup is not an active control failure. Never clear
                // an existing abort or recover an acquired/armed session here.
                if(acquisition_epoch_==0 && !release_attempted_ &&
                   !ri_ptr_->IsControlRequestSent() && current_state_name_==kIdle &&
                   !stand_armed_ && !stand_pending_ && !stand_active_) {
                    software_velocity_interface_->stop();
                    ri_ptr_->SetJointCommandEnabled(false);
                    StandStatus("WAITING_FOR_TELEMETRY");
                    return true;
                }
                const auto sample=ri_ptr_->GetStandFeedback();
                AbortStandLocked(sample.valid ? "stale telemetry" : "invalid measured feedback"); return true;
            }
            if(stand_status_=="WAITING_FOR_TELEMETRY") StandStatus("LOCKED");
            if(rl_forward_active_) {
                const char* failure=rl_forward_permit_?rl_forward_permit_->FailureReason():"RL forward permit missing";
                if(failure){AbortStandLocked(failure);return true;}
                const double elapsed=stand_now_()-rl_forward_started_;
                if(elapsed>=5.0){AbortStandLocked("RL forward 5s deadline");return true;}
                const float expected=elapsed>=1.0&&elapsed<2.0?0.25f:0.0f;
                if(!software_velocity_interface_->SetSupervisedForward(expected)) {
                    AbortStandLocked("RL forward command gate failure");return true;
                }
                if(expected>0 && !forward_pulse_seen_){forward_pulse_seen_=true;StandStatus("RL_FORWARD_PULSE");
                    ri_ptr_->RecordStandEvent(3,"forward command became +0.25");}
                if(expected==0 && forward_pulse_seen_ && stand_status_!="RL_FORWARD_ZERO_HOLD"){
                    StandStatus("RL_FORWARD_ZERO_HOLD");ri_ptr_->RecordStandEvent(3,"forward command returned to zero");}
                const auto cmd=software_velocity_interface_->VelocitySnapshot();
                const auto s=ri_ptr_->GetStandFeedback();
                if(current_state_name_!=kRLControl || current_controller_!=rl_controller_ ||
                   !ri_ptr_->IsControlRequestSent() || !ri_ptr_->JointCommandsEnabled() ||
                   cmd.forward_vel_scale!=expected || cmd.side_vel_scale!=0 || cmd.turnning_vel_scale!=0 ||
                   !s.valid || !s.fresh || !s.q.allFinite() || !s.dq.allFinite() || !s.rpy.allFinite() ||
                   std::abs(s.rpy[0])>.35 || std::abs(s.rpy[1])>.35 || current_controller_->LoseControlJudge()){
                    AbortStandLocked("RL forward guard/state failure");return true;
                }
                const auto target=ri_ptr_->GetJointCommand();
                if(target.rows()!=12 || target.cols()!=5 || !target.allFinite() ||
                   (target.col(1)-s.q).cwiseAbs().maxCoeff()>.35){AbortStandLocked("RL forward tracking failure");return true;}
                const auto stamp=ri_ptr_->GetInterfaceTimeStamp();
                if(stamp!=time_record_){time_record_=stamp;ri_ptr_->SetStandDiagnosticContext(elapsed);
                    if(AbortRequested()){AbortStandLocked("abort before RL forward update");return true;}
                    current_controller_->Run();}
                return true;
            }
            if(rl_zero_active_) {
                const auto cmd=software_velocity_interface_->VelocitySnapshot();
                const auto s=ri_ptr_->GetStandFeedback();
                const char* permit_failure=rl_zero_permit_?rl_zero_permit_->FailureReason():"RL zero permit missing";
                if(permit_failure) {AbortStandLocked(permit_failure);return true;}
                if(stand_now_()-rl_zero_started_>=8.0) {AbortStandLocked("RL zero 8s deadline");return true;}
                if(current_state_name_!=kRLControl || current_controller_!=rl_controller_ ||
                   !ri_ptr_->IsControlRequestSent() || !ri_ptr_->JointCommandsEnabled() ||
                   cmd.forward_vel_scale!=0 || cmd.side_vel_scale!=0 || cmd.turnning_vel_scale!=0 ||
                   !s.valid || !s.fresh || !s.q.allFinite() || !s.dq.allFinite() || !s.rpy.allFinite() ||
                   std::abs(s.rpy[0])>.35 || std::abs(s.rpy[1])>.35 || current_controller_->LoseControlJudge()) {
                    AbortStandLocked("RL zero guard/state failure");return true;
                }
                const auto target=ri_ptr_->GetJointCommand();
                if(target.rows()!=12 || target.cols()!=5 || !target.allFinite() ||
                   (target.col(1)-s.q).cwiseAbs().maxCoeff()>.35) {
                    AbortStandLocked("RL zero tracking failure");return true;
                }
                const auto stamp=ri_ptr_->GetInterfaceTimeStamp();
                if(stamp!=time_record_) {
                    time_record_=stamp;
                    ri_ptr_->SetStandDiagnosticContext(stand_now_()-rl_zero_started_);
                    if(AbortRequested()) {AbortStandLocked("abort before RL zero update");return true;}
                    current_controller_->Run();
                }
                return true;
            }
            if((stand_armed_ || stand_pending_) && stand_now_()>=arm_deadline_) {
                AbortStandLocked("stand authorization expired"); return true;
            }
            const auto stamp=ri_ptr_->GetInterfaceTimeStamp();
            const bool new_feedback=stamp!=time_record_;
            if(stand_active_) {
                if(current_controller_!=standup_controller_ || current_state_name_!=kStandUp ||
                   !ri_ptr_->IsControlRequestSent() || !ri_ptr_->JointCommandsEnabled()) {
                    AbortStandLocked("stand gate/state lost"); return true;
                }
                if(supported_leg_test_active_) {
                    if(!SupportedLegTestGuard()) {
                        AbortStandLocked("supported leg test guard failure"); return true;
                    }
                    StandStatus(SupportedLegPhaseStatus());
                } else {
                    const auto result=stand_monitor_.Check(stand_now_(),StandSample(new_feedback));
                    ri_ptr_->SetStandMonitorDiagnostics(stand_monitor_.diagnostics());
                    if(result==supervised_stand::Result::Abort) {
                        AbortStandLocked(stand_monitor_.reason()); return true;
                    }
                    if(result==supervised_stand::Result::TargetReached && new_feedback) {
                        const auto now=stand_now_();
                        if(supported_leg_test_finishing_) {
                            AbortStandLocked("supported leg lift complete"); return true;
                        }
                        if(supported_leg_test_requested_) {
                            if(!stand_permit_ || !stand_permit_->RenewSupportedHold() ||
                               !ri_ptr_->EnableSupportedLegTestBounds(true) ||
                               !typed_standup_controller_->BeginSupportedLegLift()) {
                                AbortStandLocked("supported leg test entry failed"); return true;
                            }
                            supported_leg_test_requested_=false;
                            supported_leg_test_active_=true;
                            supported_leg_test_have_command_=false;
                            supported_leg_test_started_=now;
                            target_reached_started_=-1.0;
                            ri_ptr_->RecordStandEvent(1,
                                "supported leg test: 5mm body shift, 2mm FR lift, 0.25s hold");
                            StandStatus("LEG_TEST_SHIFT_BODY");
                        } else {
                            if(target_reached_started_<0) target_reached_started_=now;
                            if(now-target_reached_started_>=2.0) {
                                AbortStandLocked("stand target hold complete"); return true;
                            }
                            if(!stand_permit_ || !stand_permit_->RenewSupportedHold()) {
                                AbortStandLocked("stand hold permit expired or cancelled"); return true;
                            }
                            StandStatus("TARGET_REACHED");
                        }
                    } else if(!supported_leg_test_finishing_) {
                        StandStatus(result==supervised_stand::Result::TargetReached ?
                            "TARGET_REACHED" : "STANDING_UP");
                    }
                }
            }
            if(!new_feedback) return true;
            time_record_=stamp;
            if(AbortRequested()) { AbortStandLocked("abort before trajectory"); return true; }
            if(stand_active_) {
                // No transition to RL/damping/idle through the ordinary state machine.
                current_controller_->Run();
                if(!ri_ptr_->JointCommandsEnabled()) {
                    const auto reason=std::string("send guard: ")+ri_ptr_->LastStandSendReason();
                    AbortStandLocked(reason.c_str()); return true;
                }
                have_stand_command_=true; last_command_stamp_=stamp;
                if(supported_leg_test_active_) {
                    supported_leg_test_have_command_=true;
                    const auto command=ri_ptr_->GetJointCommand();
                    if(!typed_standup_controller_->SupportedLegLiftCommandWithinBounds(command)) {
                        AbortStandLocked("supported leg test command bounds"); return true;
                    }
                    if(typed_standup_controller_->SupportedLegLiftComplete()) {
                        supported_leg_test_active_=false;
                        supported_leg_test_finishing_=true;
                        supported_leg_test_have_command_=false;
                        stand_monitor_.Start(stand_now_());
                        ri_ptr_->RecordStandEvent(1,
                            "supported leg test recentered; verifying stand");
                        StandStatus("LEG_TEST_VERIFY_STAND");
                    } else StandStatus(SupportedLegPhaseStatus());
                }
                return true;
            }
            if(current_state_name_!=kIdle) { AbortStandLocked("unauthorized controller"); return true; }
            current_controller_->Run(); // idle packets remain gate-blocked
            const auto next=current_controller_->GetNextStateName();
            if(next==kStandUp && stand_pending_) {
                if(AbortRequested() || stand_now_()>=arm_deadline_ || !StandPreflight()) { AbortStandLocked("entry preflight failed"); return true; }
                ri_ptr_->SetJointCommandEnabled(false);
                current_controller_->OnExit();
                current_controller_=standup_controller_;
                current_state_name_=next_state_name_=kStandUp;
                current_controller_->OnEnter();
                // Recheck after OnEnter; it never opens the actuator gate itself.
                if(AbortRequested() || stand_now_()>=arm_deadline_ || !StandPreflight()) { AbortStandLocked("entry aborted"); return true; }
                stand_monitor_.Start(stand_now_());
                target_reached_started_=-1.0;
                stand_robot_start_=ri_ptr_->GetInterfaceTimeStamp();
                have_stand_command_=false;
                stand_permit_=std::shared_ptr<const StandOnlyPermit>(new StandOnlyPermit(
                    abort_requested_,shutdown_signal_,std::chrono::steady_clock::now()+StandOnlyPermit::lifetime));
                if(!ri_ptr_->OpenSupervisedStand(stand_permit_)) { AbortStandLocked("stand grant rejected"); return true; }
                stand_pending_=false; stand_active_=true;
                ri_ptr_->RecordStandEvent(1,"stand entry");
                StandStatus("STANDING_UP");
            } else if(next!=kIdle) { AbortStandLocked("unauthorized transition"); }
            return true;
        } catch(...) {
            AbortStandLocked("stand/control exception");
            throw;
        }
    }
    void Run(const volatile std::sig_atomic_t* stop_signal = nullptr,
             const std::atomic<bool>* asynchronous_signal = nullptr) {
        { std::lock_guard<std::mutex> lock(lifecycle_mutex_); shutdown_signal_=asynchronous_signal; }
        try {
            while ((!stop_signal || *stop_signal == 0) &&
                   (!asynchronous_signal || !asynchronous_signal->load())) {
                if (!ProcessOnce()) break;
                std::this_thread::sleep_for(std::chrono::microseconds(500));
            }
        } catch (...) {
            Shutdown();
            throw;
        }
        Shutdown();
    }
};
