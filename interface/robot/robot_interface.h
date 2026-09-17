/**
 * @file robot_interface.h
 * @brief this file is for applying robot's control interface
 * @author mazunwang
 * @version 1.0
 * @date 2024-04-11
 * 
 * @copyright Copyright (c) 2024  DeepRobotics
 * 
 */
#pragma once

#include "common_types.h"
#include <atomic>
#include "stand_only_permit.hpp"
#include "rl_zero_permit.hpp"
#include "rl_forward_permit.hpp"
#include "stand_diagnostics.hpp"

using namespace types;

namespace interface{
class RobotInterface{
    friend class ::StateMachine;
protected:
    virtual bool OpenSupervisedStand(const std::shared_ptr<const StandOnlyPermit>&) { return false; }
    virtual bool EnableSupportedLegTestBounds(bool) { return false; }
    virtual bool OpenSupervisedRLZero(const std::shared_ptr<const RLZeroPermit>&) { return false; }
    virtual bool OpenSupervisedRLForward(const std::shared_ptr<const RLForwardPermit>&) { return false; }
private:
    /* data */
public:
    /**
     * @brief Construct a new Robot Interface object
     * @param  robot_name       robot name
     * @param  dof_num          The number of degrees of freedom of the robot.
     */
    RobotInterface(const std::string& robot_name, int dof_num):robot_name_(robot_name), dof_num_(dof_num){
        start_flag_ = true;
    }
    virtual ~RobotInterface(){};

    std::string robot_name_;
    const int dof_num_;
    Eigen::Matrix<float, Eigen::Dynamic, 5> joint_cmd_;
    std::atomic<bool> start_flag_;

    /**
     * @brief Start to get robot's state and send control command
     */
    virtual void Start() = 0;

    /**
     * @brief Stop to control the robot
     */
    virtual void Stop() = 0;

    // Hardware implementations may require an explicit ownership handoff.
    // Simulation backends remain passive and can use the default no-op result.
    virtual bool AcquireControl() { return true; }
    virtual void ReleaseControl() {}
    virtual bool IsControlAcquired() const { return false; }
    virtual bool IsControlRequestSent() const { return IsControlAcquired(); }
    virtual const char* OwnershipStatus() const { return "OWNERSHIP_UNCONFIRMED"; }
    virtual bool IsFeedbackFresh() const { return true; }
    virtual double FeedbackAgeSeconds() const { return 0.0; }
    virtual void SetJointCommandEnabled(bool) {}
    virtual bool JointCommandsEnabled() const { return false; }
    struct StandFeedback {
        VecXf q, dq, torque;
        Vec3f rpy;
        double stamp=0, age=0;
        bool fresh=false;
        bool valid=true;
    };
    virtual StandFeedback GetStandFeedback() {
        return {GetJointPosition(),GetJointVelocity(),GetJointTorque(),GetImuRpy(),
                GetInterfaceTimeStamp(),FeedbackAgeSeconds(),IsFeedbackFresh()};
    }
    virtual void SetStandDiagnosticContext(double) {}
    virtual void SetStandMonitorDiagnostics(const stand_diagnostics::MonitorStatus&) {}
    // Log-only metadata. Never a source for feedback, freshness or guard checks.
    virtual void RecordStandEntryMetadata(const VecXf&, const VecXf&, double) {}
    virtual std::string LastStandSendReason() const { return "OTHER"; }
    virtual void FinishStandDiagnostics(const std::string&) {}
    virtual void RecordStandEvent(int, const std::string&) {}
    virtual void RecordPolicyProgress(const Vec3f&, bool) {} // diagnostic only
    virtual void RecordPolicySnapshot(const std::array<double,45>&,
                                      const std::array<double,12>&) {} // diagnostic only

    /**
     * @brief Get the time stamp of the robot
     * @return double        time stamp
     */
    virtual double GetInterfaceTimeStamp() = 0;

    /**
     * @brief Get the joint position of the robot
     * @return VecXf        joint position vector
     */
    virtual VecXf GetJointPosition() = 0;

    /**
     * @brief Get the joint velocity of the robot
     * @return VecXf        joint velocity vector
     */
    virtual VecXf GetJointVelocity() = 0;

    /**
     * @brief Get the joint torque of the robot
     * @return VecXf        joint torque vector
     */
    virtual VecXf GetJointTorque() = 0;

    /**
     * @brief Get the roll-pitch-yaw angle of the robot base
     * @return Vec3f        roll-pitch-yaw(unit rad)
     */
    virtual Vec3f GetImuRpy() = 0;

    /**
     * @brief Get the accleration of the robot base
     * @return Vec3f        accleration(unit m*s^-2)
     */
    virtual Vec3f GetImuAcc() = 0;

    /**
     * @brief Get the angular velocity of robot base
     * @return Vec3f        angular velocity in body coordinate(unit rad/s)
     */
    virtual Vec3f GetImuOmega() = 0;

    /**
     * @brief Set the joint command in standard form
     *                  torque = kp * (qDes - q) + kd * (vDes - v) + tff
     * @param  input       a dof_num*5 matrix and each column represent kp, goal_angle_pos, kd, goal_vel, torque_feedforward 
     * (current torque, not last torque, video content slip of the tongue)
     */
    virtual void SetJointCommand(Eigen::Matrix<float, Eigen::Dynamic, 5> input) = 0;

    virtual MatXf GetJointCommand(){
        return joint_cmd_;
    }

    /**
     * @brief Get the contact force if robot have any force sensor
     * @return VecXf        force vector
     */
    virtual VecXf GetContactForce() = 0;

    /**
     * @brief Get the motor temperture 
     * @return VecXf        motor temperture
     */
    virtual VecXf GetMotorTemperture(){
        return VecXf::Zero(dof_num_);
    }

    /**
     * @brief Get the driver temperture 
     * @return VecXf        driver temperture
     */
    virtual VecXf GetDriverTemperture(){
        return VecXf::Zero(dof_num_);
    }
};


};//namespace interface
