/**
 * @file rl_control_state_onnx.hpp
 * @brief rl policy runnning state using onnx
 * @author Bo (Percy) Peng
 * @version 1.0
 * @date 2025-08-10
 * 
 * @copyright Copyright (c) 2025  DeepRobotics
 * 
 */




#pragma once

#include "state_base.h"
#include "policy_runner_base.hpp"
#include "lite3_test_policy_runner_onnx.h"
#include <atomic>
#include <mutex>



class RLControlStateONNX : public StateBase
{
private:
    RobotBasicState rbs_{};
    int state_run_cnt_{-1};
    std::mutex observation_mutex_;

    std::shared_ptr<PolicyRunnerBase> policy_ptr_;
    std::shared_ptr<Lite3TestPolicyRunnerONNX> test_policy_;


    
    std::thread run_policy_thread_;
    std::atomic<bool> start_flag_{false};
    std::atomic<bool> worker_failed_{false};

    std::atomic<float> policy_cost_time_{1};

    void UpdateRobotObservation(){
        rbs_.base_rpy     = ri_ptr_->GetImuRpy();
        rbs_.base_rot_mat = RpyToRm(rbs_.base_rpy);
        rbs_.projected_gravity = RmToProjectedGravity(rbs_.base_rot_mat);
        rbs_.base_omega   = ri_ptr_->GetImuOmega();
        rbs_.base_acc     = ri_ptr_->GetImuAcc();
        rbs_.joint_pos    = ri_ptr_->GetJointPosition();
        rbs_.joint_vel    = ri_ptr_->GetJointVelocity();
        rbs_.joint_tau    = ri_ptr_->GetJointTorque();
        // static Vec3f cmd_vel;
        // Vec3f cmd_vel_input = Vec3f(uc_ptr_->GetUserCommand().forward_vel_scale, 
        //                             uc_ptr_->GetUserCommand().side_vel_scale, 
        //                             uc_ptr_->GetUserCommand().turnning_vel_scale);

        // Eigen::Vector3f vel_delta = cmd_vel_input - cmd_vel;
        // const Eigen::Vector3f vel_delta_const(0.0015, 0.001, 0.0012);
        // for(int i=0;i<3;++i){
        //     if(fabs(vel_delta(i)) > vel_delta_const(i)) vel_delta(i) = Sign(vel_delta(i))*vel_delta_const(i);
        // }
        // cmd_vel+=vel_delta;           
        // rbs_.cmd_vel_normlized = cmd_vel;
        const auto command = uc_ptr_->GetUserCommand();
        rbs_.cmd_vel_normlized = Vec3f(command.forward_vel_scale,
                                    command.side_vel_scale, command.turnning_vel_scale);
        
    }

    void PolicyRunner(){
        int run_cnt_record = -1;
        try {
        while (start_flag_.load()){
            std::unique_lock<std::mutex> lock(observation_mutex_);
            if(state_run_cnt_%policy_ptr_->decimation_ == 0 && state_run_cnt_ != run_cnt_record){
                timespec start_timestamp, end_timestamp;
                clock_gettime(CLOCK_MONOTONIC,&start_timestamp);
                // Re-read the command at inference time so stop/timeout cannot
                // leave a cached nonzero velocity in the worker's observation.
                const auto command = uc_ptr_->GetUserCommand();
                rbs_.cmd_vel_normlized = Vec3f(command.forward_vel_scale,
                    command.side_vel_scale, command.turnning_vel_scale);
                ri_ptr_->RecordPolicyProgress(rbs_.cmd_vel_normlized,false);
                auto ra = policy_ptr_->GetRobotAction(rbs_);
                std::array<double,45> policy_observation{};
                std::array<double,12> policy_raw_action{};
                if(policy_ptr_->GetDiagnosticSnapshot(policy_observation,policy_raw_action))
                    ri_ptr_->RecordPolicySnapshot(policy_observation,policy_raw_action);
                ri_ptr_->RecordPolicyProgress(rbs_.cmd_vel_normlized,true);
                MatXf res = ra.ConvertToMat();
                if (start_flag_.load()) ri_ptr_->SetJointCommand(res);
                run_cnt_record = state_run_cnt_;
                clock_gettime(CLOCK_MONOTONIC,&end_timestamp);
                policy_cost_time_ = (end_timestamp.tv_sec-start_timestamp.tv_sec)*1e3 
                                    +(end_timestamp.tv_nsec-start_timestamp.tv_nsec)/1e6;
                // std::cout << "cost_time:  " << policy_cost_time_ << " ms\n";
            }
            lock.unlock();
            std::this_thread::sleep_for(std::chrono::microseconds(100));
        }
        } catch (...) {
            worker_failed_ = true;
            start_flag_ = false;
            uc_ptr_->Stop();
            ri_ptr_->SetJointCommandEnabled(false);
        }
    }

public:
    RLControlStateONNX(const RobotType& robot_type, const std::string& state_name, 
        std::shared_ptr<ControllerData> data_ptr):StateBase(robot_type, state_name, data_ptr){
        test_policy_ = std::make_shared<Lite3TestPolicyRunnerONNX>("test_onnx");
        policy_ptr_ = test_policy_;
        if(!policy_ptr_){
            std::cerr << "[ERROR] Failed to initialize ONNX policy runner." << std::endl;
            exit(0);
        }  
        policy_ptr_->DisplayPolicyInfo();
        }
    // Test seam uses the same worker lifecycle with an inert policy.
    RLControlStateONNX(const RobotType& robot_type, const std::string& state_name,
        std::shared_ptr<ControllerData> data_ptr, std::shared_ptr<PolicyRunnerBase> policy)
        : StateBase(robot_type, state_name, data_ptr), policy_ptr_(std::move(policy)) {}
    ~RLControlStateONNX(){ OnExit(); }

    virtual void OnEnter() {
        OnExit();
        state_run_cnt_ = -1;
        worker_failed_ = false;
        policy_ptr_->OnEnter();
        StateBase::msfb_.UpdateCurrentState(RobotMotionState::RLControlMode);
        uc_ptr_->SetMotionStateFeedback(StateBase::msfb_);
        start_flag_ = true;
        run_policy_thread_ = std::thread(std::bind(&RLControlStateONNX::PolicyRunner, this));
    };

    virtual void OnExit() { 
        start_flag_ = false;
        if (run_policy_thread_.joinable()) run_policy_thread_.join();
        state_run_cnt_ = -1;
    }

    virtual void Run() {
        std::lock_guard<std::mutex> lock(observation_mutex_);
        UpdateRobotObservation();
        if (ds_ptr_) ds_ptr_->InsertScopeData(0, policy_cost_time_.load());
        state_run_cnt_++;
    }

    virtual bool LoseControlJudge() {
        if (worker_failed_.load()) return true;
        if(uc_ptr_->GetUserCommand().target_mode == int(RobotMotionState::JointDamping)) return true;
        return PostureUnsafeCheck();
    }

    bool PostureUnsafeCheck(){
        Vec3f rpy = ri_ptr_->GetImuRpy();
        if(fabs(rpy(0)) > 30./180*M_PI || fabs(rpy(1)) > 45./180*M_PI){
            std::cout << "posture value: " << 180./M_PI*rpy.transpose() << std::endl;
            return true;
        }
        return false;
    }

    virtual StateName GetNextStateName() {
        return StateName::kRLControl;
    }
};
