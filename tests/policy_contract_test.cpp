#include "lite3_test_policy_runner_onnx.h"

#include <array>
#include <cmath>
#include <iostream>
#include <stdexcept>

namespace {
void Check(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

RobotBasicState StandingState(float command) {
    RobotBasicState state{};
    state.base_rot_mat = Mat3f::Identity();
    state.base_omega = Vec3f::Zero();
    state.joint_pos = VecXf(12);
    state.joint_vel = VecXf::Zero(12);
    state.joint_tau = VecXf::Zero(12);
    for (int leg = 0; leg < 4; ++leg) {
        state.joint_pos[3 * leg] = 0.0f;
        state.joint_pos[3 * leg + 1] = -0.80f;
        state.joint_pos[3 * leg + 2] = 1.60f;
    }
    state.cmd_vel_normlized = Vec3f(command, 0.0f, 0.0f);
    return state;
}
}

int main() {
    try {
        Lite3TestPolicyRunnerONNX policy("policy-contract");
        Check(policy.decimation_ == 12,
              "official 2025 real-Lite3 policy must run every 12 one-ms feedback ticks");

        auto state = StandingState(0.25f);
        policy.OnEnter();
        policy.GetRobotAction(state);

        std::array<double, 45> observation{};
        std::array<double, 12> action{};
        Check(policy.GetDiagnosticSnapshot(observation, action), "first snapshot unavailable");
        Check(std::abs(observation[6] - 0.20) < 1e-6,
              "forward command scaling changed");

        // A new policy session must not inherit the previous session's action.
        policy.OnEnter();
        state.cmd_vel_normlized.setZero();
        policy.GetRobotAction(state);
        Check(policy.GetDiagnosticSnapshot(observation, action), "reset snapshot unavailable");
        for (int i = 33; i < 45; ++i)
            Check(observation[i] == 0.0, "last-action observation was not reset");

        std::cout << "PASS: restored real-Lite3 policy contract and clean entry state\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}
