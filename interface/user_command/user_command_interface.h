/**
 * @file user_command_interface.h
 * @brief this file is used for robot's user command input
 * @author mazunwang
 * @version 1.0
 * @date 2024-04-11
 * 
 * @copyright Copyright (c) 2024  DeepRobotics
 * 
 */
#pragma once

#include "common_types.h"
#include "custom_types.h"

using namespace types;

namespace interface{

class UserCommandInterface{
private:
    /* data */
public:
    UserCommandInterface(){}
    ~UserCommandInterface(){}

    /**
     * @brief start the thread to process user command
     */
    virtual void Start() = 0;

    /**
     * @brief stop the thread 
     */
    virtual void Stop() = 0;

    /**
     * @brief return your user command
     * @return UserCommand 
     */
    virtual UserCommand GetUserCommand() = 0; 

    /**
     * @brief set the motion state feedback 
     * @param  msfb         motion state feedback
     */
    virtual void SetMotionStateFeedback(const MotionStateFeedback& msfb) = 0;

    /** True while the input source is usable. Passive/software sources keep
     * the historical always-connected default. */
    virtual bool IsConnected() const { return true; }

    MotionStateFeedback msfb_;
};
};
