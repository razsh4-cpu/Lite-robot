/**
 * @file standup_state.hpp
 * @brief from sit state to stand state
 * @author mazunwang
 * @version 1.0
 * @date 2024-05-29
 * 
 * @copyright Copyright (c) 2024  DeepRobotics
 * 
 */
#pragma once

#include "state_base.h"
#include "supported_leg_lift_plan.hpp"

class StandUpState : public StateBase{
private:
    VecXf init_joint_pos_, init_joint_vel_, current_joint_pos_, current_joint_vel_;
    double time_stamp_record_, run_time_;
    VecXf goal_joint_pos_, kp_, kd_;
    MatXf joint_cmd_;
    float stand_duration_ = 2.;
    SupportedLegLiftPlan supported_leg_lift_plan_;
    bool supported_leg_lift_active_{false};
    bool supported_leg_lift_complete_{false};
    double supported_leg_lift_start_{0.0};
    SupportedLegLiftPlan::Phase supported_leg_lift_phase_{SupportedLegLiftPlan::Phase::Complete};

    void GetRobotJointValue(){
        const auto sample = ri_ptr_->GetStandFeedback();
        current_joint_pos_ = sample.q;
        current_joint_vel_ = sample.dq;
        run_time_ = sample.stamp;
    }

    void RecordJointData(){
        init_joint_pos_ = current_joint_pos_;
        init_joint_vel_ = current_joint_vel_;
        time_stamp_record_ = run_time_;
    }

    float GetCubicSplinePos(float x0, float v0, float xf, float vf, float t, float T){
        if(t >= T) return xf;
        float a, b, c, d;
        d = x0;
        c = v0;
        a = (vf*T - 2*xf + v0*T + 2*x0) / pow(T, 3);
        b = (3*xf - vf*T - 2*v0*T - 3*x0) / pow(T, 2);
        return a*pow(t, 3)+b*pow(t, 2)+c*t+d;
    }
    float GetCubicSplineVel(float x0, float v0, float xf, float vf, float t, float T){
        if(t >= T) return 0;
        float a, b, c;
        c = v0;
        a = (vf*T - 2*xf + v0*T + 2*x0) / pow(T, 3);
        b = (3*xf - vf*T - 2*v0*T - 3*x0) / pow(T, 2);
        return 3.*a*pow(t, 2) + 2.*b*t + c;
    }

    float GetHipYPosByHeight(float h){
        float l1 = cp_ptr_->thigh_len_;
        float l2 = cp_ptr_->shank_len_;
        float default_pos = (cp_ptr_->fl_joint_lower_(1)+cp_ptr_->fl_joint_upper_(1)) / 2.;
        if(fabs(h) >= l1 + l2) {
            std::cerr << "error height input" << std::endl;
            return 0;
        }
        float theta = -acos((l1*l1+h*h-l2*l2)/(2.*h*l1));
        theta = LimitNumber(theta, cp_ptr_->fl_joint_lower_(1), cp_ptr_->fl_joint_upper_(1));
        return theta;
    }

    float GetKneePosByHeight(float h){
        float l1 = cp_ptr_->thigh_len_;
        float l2 = cp_ptr_->shank_len_;
        float default_pos = (cp_ptr_->fl_joint_lower_(2)+cp_ptr_->fl_joint_upper_(2)) / 2.;
        if(fabs(h) >= l1 + l2) {
            std::cerr << "error height input" << std::endl;
            return 0;
        }
        float theta = M_PI-acos((l1*l1+l2*l2-h*h)/(2*l1*l2));
        theta = LimitNumber(theta, cp_ptr_->fl_joint_lower_(2), cp_ptr_->fl_joint_upper_(2));
        return theta;
    }

public:
    StandUpState(const RobotType& robot_type, const std::string& state_name, 
        std::shared_ptr<ControllerData> data_ptr):StateBase(robot_type, state_name, data_ptr){
            goal_joint_pos_ = Vec3f(0., GetHipYPosByHeight(cp_ptr_->pre_height_), GetKneePosByHeight(cp_ptr_->pre_height_)).replicate(4, 1);
            kp_ = VecXf(12);
            kd_ = VecXf(12);     
            kp_ = cp_ptr_->swing_leg_kp_.replicate(4, 1);
            kd_ = cp_ptr_->swing_leg_kd_.replicate(4, 1);
            joint_cmd_ = MatXf::Zero(12, 5);
            joint_cmd_.col(0) = kp_;
            joint_cmd_.col(2) = kd_;
            stand_duration_ = cp_ptr_->stand_duration_;
        }
    ~StandUpState(){}


    virtual void OnEnter() {
        supported_leg_lift_active_=false;
        supported_leg_lift_complete_=false;
        supported_leg_lift_phase_=SupportedLegLiftPlan::Phase::Complete;
        GetRobotJointValue();
        RecordJointData();
        ri_ptr_->RecordStandEntryMetadata(init_joint_pos_, init_joint_vel_, time_stamp_record_);
        StateBase::msfb_.UpdateCurrentState(RobotMotionState::StandingUp);
        uc_ptr_->SetMotionStateFeedback(StateBase::msfb_);
    };
    virtual void OnExit() {
        supported_leg_lift_active_=false;
    }
    virtual void Run() {
        GetRobotJointValue();
        if(supported_leg_lift_active_){
            const auto sample=supported_leg_lift_plan_.At(run_time_-supported_leg_lift_start_);
            joint_cmd_=sample.command;
            if(!SupportedLegLiftCommandWithinBounds(joint_cmd_))
                throw std::runtime_error("supported leg test planner exceeded command bounds");
            supported_leg_lift_phase_=sample.phase;
            supported_leg_lift_complete_=sample.complete;
            ri_ptr_->SetStandDiagnosticContext(run_time_-time_stamp_record_);
            ri_ptr_->SetJointCommand(joint_cmd_);
            return;
        }
        VecXf planning_joint_pos(current_joint_pos_.rows());
        VecXf planning_joint_vel(current_joint_pos_.rows());
        if(run_time_ - time_stamp_record_ <= stand_duration_){
            for(int i=0;i<current_joint_pos_.rows();++i){
                planning_joint_pos(i) = GetCubicSplinePos(init_joint_pos_(i), init_joint_vel_(i), goal_joint_pos_(i), 0, 
                                                run_time_ - time_stamp_record_, stand_duration_);
                planning_joint_vel(i) = GetCubicSplineVel(init_joint_pos_(i), init_joint_vel_(i), goal_joint_pos_(i), 0, 
                                                run_time_ - time_stamp_record_, stand_duration_);
            }
        }else{
            float new_time = run_time_ - time_stamp_record_ - stand_duration_;
            float dt = 0.001;
            float plan_height = GetCubicSplinePos(cp_ptr_->pre_height_, 0, cp_ptr_->stand_height_, 0, 
                                                new_time, stand_duration_);
            float plan_height_next = GetCubicSplinePos(cp_ptr_->pre_height_, 0, cp_ptr_->stand_height_, 0, 
                                                new_time+dt, stand_duration_);
            float hipy_pos = GetHipYPosByHeight(plan_height);
            float hipy_vel = (GetHipYPosByHeight(plan_height_next) - hipy_pos) / dt;
            float knee_pos = GetKneePosByHeight(plan_height);
            float knee_vel = (GetKneePosByHeight(plan_height_next) - knee_pos) / dt;
            planning_joint_pos = Vec3f(0, hipy_pos, knee_pos).replicate(4, 1);
            planning_joint_vel = Vec3f(0, hipy_vel, knee_vel).replicate(4, 1);

            // std::cout << "planning_pos:  " << planning_joint_pos.transpose() << std::endl;
        }

        joint_cmd_.col(1) = planning_joint_pos;
        joint_cmd_.col(3) = planning_joint_vel;
        ri_ptr_->SetStandDiagnosticContext(run_time_ - time_stamp_record_);
        ri_ptr_->SetJointCommand(joint_cmd_); // (current torque, not last torque, video content slip of the tongue)
    }
    bool BeginSupportedLegLift(){
        if(supported_leg_lift_active_ || supported_leg_lift_complete_) return false;
        GetRobotJointValue();
        supported_leg_lift_start_=run_time_;
        supported_leg_lift_phase_=SupportedLegLiftPlan::Phase::ShiftBody;
        supported_leg_lift_active_=true;
        return true;
    }
    bool SupportedLegLiftActive() const { return supported_leg_lift_active_; }
    bool SupportedLegLiftComplete() const { return supported_leg_lift_complete_; }
    SupportedLegLiftPlan::Phase SupportedLegLiftPhase() const { return supported_leg_lift_phase_; }
    bool SupportedLegLiftCommandWithinBounds(const MatXf& command) const {
        if(command.rows()!=12 || command.cols()!=5 || !command.allFinite()) return false;
        for(int i=0;i<12;++i){
            const double stand=supported_leg_lift_plan_.stand()[i/3][i%3];
            if(command(i,0)<0 || command(i,0)>SupportedLegLiftPlan::kKp+1e-4 ||
               command(i,2)<0 || command(i,2)>SupportedLegLiftPlan::kKd+1e-4 ||
               std::abs(command(i,1)-stand)>0.0300001 ||
               std::abs(command(i,3))>0.1000001 || command(i,4)!=0) return false;
        }
        return true;
    }
    virtual bool LoseControlJudge() {
        if(uc_ptr_->GetUserCommand().target_mode == int(RobotMotionState::JointDamping)) return true;
        return false;
    }
    virtual StateName GetNextStateName() {
        if(run_time_ - time_stamp_record_ <= 2.*stand_duration_){
            return StateName::kStandUp;
        }else{
            if(uc_ptr_->GetUserCommand().target_mode == int(RobotMotionState::RLControlMode)){
                return StateName::kRLControl;
                std::cout << "stand up success" << std::endl;
            }
        }
        return StateName::kStandUp;
    }
};
