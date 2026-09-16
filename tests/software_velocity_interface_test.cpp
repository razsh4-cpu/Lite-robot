#include "software_velocity_interface.hpp"

#include <chrono>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <thread>

namespace {
void Require(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        std::exit(1);
    }
}

bool Near(float value, float expected) {
    return std::fabs(value - expected) < 1e-6f;
}

types::MotionStateFeedback State(int value) {
    types::MotionStateFeedback feedback;
    feedback.UpdateCurrentState(value);
    return feedback;
}

void RequireZero(const types::UserCommand& command, const char* message) {
    Require(Near(command.forward_vel_scale, 0.0f) &&
            Near(command.side_vel_scale, 0.0f) &&
            Near(command.turnning_vel_scale, 0.0f), message);
}
}  // namespace

int main() {
    SoftwareVelocityInterface input(std::chrono::milliseconds(20));
    input.Start();
    RequireZero(input.GetUserCommand(), "initial velocity must be zero");

    input.SetMotionStateFeedback(State(types::RobotMotionState::WaitingForStand));
    input.set_velocity_normalized(0.4f, 0.3f, -0.2f);
    RequireZero(input.GetUserCommand(), "motion outside RL mode must be blocked");

    Require(input.request_stand(), "stand request must be accepted from WaitingForStand");
    Require(input.GetUserCommand().target_mode == types::RobotMotionState::StandingUp,
            "stand request must target StandingUp only from WaitingForStand");

    input.SetMotionStateFeedback(State(types::RobotMotionState::StandingUp));
    Require(input.request_rl_control(), "RL request must be accepted from StandingUp");
    Require(input.GetUserCommand().target_mode == types::RobotMotionState::RLControlMode,
            "RL request must target RLControlMode only from StandingUp");

    input.SetMotionStateFeedback(State(types::RobotMotionState::RLControlMode));
    Require(!input.request_rl_control(), "RL request must be rejected outside StandingUp");
    input.set_velocity_normalized(2.0f, -2.0f, 0.25f);
    auto command = input.GetUserCommand();
    Require(Near(command.forward_vel_scale, 1.0f), "forward must clamp high");
    Require(Near(command.side_vel_scale, -1.0f), "lateral must clamp low");
    Require(Near(command.turnning_vel_scale, 0.25f), "yaw axis mapping must be independent");

    input.set_velocity_normalized(0.4f, 0.0f, 0.0f);
    command = input.GetUserCommand();
    Require(Near(command.forward_vel_scale, 0.4f) && Near(command.side_vel_scale, 0.0f) &&
            Near(command.turnning_vel_scale, 0.0f), "forward must affect only forward");

    input.stop();
    RequireZero(input.GetUserCommand(), "stop must zero immediately");

    input.Start();
    input.SetMotionStateFeedback(State(types::RobotMotionState::RLControlMode));
    input.set_velocity_normalized(0.5f, 0.1f, -0.3f);
    std::this_thread::sleep_for(std::chrono::milliseconds(30));
    RequireZero(input.GetUserCommand(), "stale command must time out to zero");

    for (float bad : {std::numeric_limits<float>::quiet_NaN(),
                      std::numeric_limits<float>::infinity(),
                      -std::numeric_limits<float>::infinity()}) {
        for (int axis=0;axis<3;++axis) {
            float v[3]={0.2f,0.2f,0.2f}; v[axis]=bad;
            input.set_velocity_normalized(v[0],v[1],v[2]);
            RequireZero(input.GetUserCommand(), "nonfinite input must zero all axes");
        }
    }
    input.SetMotionStateFeedback(State(types::RobotMotionState::WaitingForStand));
    Require(input.request_stand(), "queue stand");
    input.stop();
    Require(input.GetUserCommand().target_mode == types::RobotMotionState::WaitingForStand,
            "stop cancels queued stand");
    input.SetMotionStateFeedback(State(types::RobotMotionState::StandingUp));
    Require(input.request_rl_control(), "queue RL");
    input.stop();
    Require(input.GetUserCommand().target_mode == types::RobotMotionState::StandingUp,
            "stop cancels queued RL");
    input.Stop();
    Require(!input.request_rl_control(), "stopped source rejects RL");
    input.SetMotionStateFeedback(State(types::RobotMotionState::WaitingForStand));
    Require(!input.request_stand(), "stopped source rejects stand");
    std::cout << "software_velocity_interface_test: PASS\n";
    return 0;
}
