#include "lite3_test_policy_runner_onnx.h"
#include "basic_function.hpp"
#include "json.hpp"

#include <array>
#include <cmath>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

using json = nlohmann::json;

struct Sample {
    double time{};
    RobotBasicState state{};
    std::array<double, 12> recorded_action{};
};

std::vector<Sample> Load(const std::string& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot open hardware trace");
    std::vector<Sample> samples;
    std::string line;
    unsigned long long previous_policy = 0;
    while (std::getline(input, line)) {
        auto record = json::parse(line);
        if (record.value("phase", "") != "RL_FORWARD" ||
            record.value("policy_snapshot_valid", 0) == 0 ||
            record.value("sent", 0) == 0) continue;
        const auto policy = record.value("policy_started", 0ULL);
        if (policy == previous_policy) continue;
        previous_policy = policy;
        const auto observation = record.at("policy_observation").get<std::vector<double>>();
        const auto normalized = record.at("normalized_command").get<std::vector<double>>();
        const auto position = record.at("position").get<std::vector<double>>();
        const auto velocity = record.at("velocity").get<std::vector<double>>();
        if (observation.size() != 45 || normalized.size() != 3 ||
            position.size() != 12 || velocity.size() != 12)
            throw std::runtime_error("bad trace dimensions");
        Sample sample;
        sample.time = record.at("elapsed_s").get<double>();
        sample.state.base_omega = Vec3f(observation[0] / .25, observation[1] / .25, observation[2] / .25);
        sample.state.base_rpy = Vec3f(record.at("roll").get<double>(), record.at("pitch").get<double>(), 0.0);
        sample.state.base_rot_mat = functions::RpyToRm(sample.state.base_rpy);
        sample.state.projected_gravity = sample.state.base_rot_mat.inverse() * Vec3f(0, 0, -1);
        sample.state.cmd_vel_normlized = Vec3f(normalized[0], normalized[1], normalized[2]);
        sample.state.joint_pos = VecXf(12);
        sample.state.joint_vel = VecXf(12);
        sample.state.joint_tau = VecXf::Zero(12);
        for (int joint = 0; joint < 12; ++joint) {
            // Reconstruct from the values actually supplied by MotionSDK.  Do
            // not invert the observation using an assumed default pose: that
            // silently became wrong when the pre-April policy contract
            // (-0.8/1.6) was restored while the stand posture remained
            // approximately -0.65/1.30.
            sample.state.joint_pos[joint] = position[joint];
            sample.state.joint_vel[joint] = velocity[joint];
            sample.recorded_action[joint] = record.at("policy_raw_action")[joint].get<double>();
        }
        samples.push_back(sample);
    }
    if (samples.empty()) throw std::runtime_error("no policy samples in trace");
    return samples;
}

struct Metrics {
    int inferences{};
    double action_rms_error{};
    double max_knee_target_span{};
};

Metrics Replay(const std::vector<Sample>& samples, double period, bool compare_recorded) {
    Lite3TestPolicyRunnerONNX policy("hardware-trace-replay");
    policy.OnEnter();
    std::array<double, 12> minimum{}, maximum{};
    minimum.fill(std::numeric_limits<double>::infinity());
    maximum.fill(-std::numeric_limits<double>::infinity());
    double next = samples.front().time;
    double squared_error = 0;
    int error_count = 0;
    Metrics metrics;
    for (const auto& sample : samples) {
        if (sample.time + 1e-9 < next) continue;
        const auto command = policy.GetRobotAction(sample.state);
        std::array<double,45> observation{};
        std::array<double,12> raw{};
        if (!policy.GetDiagnosticSnapshot(observation, raw)) throw std::runtime_error("snapshot unavailable");
        ++metrics.inferences;
        if (sample.state.cmd_vel_normlized[0] > 0) {
            for (int joint = 0; joint < 12; ++joint) {
                minimum[joint] = std::min(minimum[joint], double(command.goal_joint_pos[joint]));
                maximum[joint] = std::max(maximum[joint], double(command.goal_joint_pos[joint]));
            }
        }
        if (compare_recorded) for (int joint = 0; joint < 12; ++joint) {
            const double error = raw[joint] - sample.recorded_action[joint];
            squared_error += error * error;
            ++error_count;
        }
        next += period;
    }
    metrics.action_rms_error = error_count ? std::sqrt(squared_error / error_count) : 0;
    for (int joint : {2, 5, 8, 11})
        metrics.max_knee_target_span = std::max(metrics.max_knee_target_span, maximum[joint] - minimum[joint]);
    return metrics;
}

int main(int argc, char** argv) {
    try {
        if (argc != 2) throw std::runtime_error("usage: policy_hardware_trace_replay TRACE.jsonl");
        const auto samples = Load(argv[1]);
        const auto old_contract = Replay(samples, .012, true);
        const auto corrected_contract = Replay(samples, .020, false);
        std::cout << "old_12ms_inferences=" << old_contract.inferences
                  << " old_action_rms_replay_error=" << old_contract.action_rms_error
                  << " old_max_knee_target_span=" << old_contract.max_knee_target_span << '\n';
        std::cout << "corrected_20ms_inferences=" << corrected_contract.inferences
                  << " corrected_max_knee_target_span=" << corrected_contract.max_knee_target_span << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}
