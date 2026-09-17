#include "state_machine/supported_leg_lift_plan.hpp"

#include <cmath>
#include <iostream>
#include <stdexcept>

namespace {
void Check(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
}

int main() {
    try {
        SupportedLegLiftPlan plan;
        double max_delta = 0.0;
        double max_velocity = 0.0;
        for (int step = 0; step <= 7000; ++step) {
            const double time = step * 0.001;
            const auto sample = plan.At(time);
            Check(sample.command.allFinite(), "all samples must be finite");
            for (int joint = 0; joint < 12; ++joint) {
                const double stand = plan.stand()[joint / 3][joint % 3];
                max_delta = std::max(max_delta,
                    std::abs(static_cast<double>(sample.command(joint, 1)) - stand));
                max_velocity = std::max(max_velocity,
                    std::abs(static_cast<double>(sample.command(joint, 3))));
                Check(sample.command(joint, 0) == SupportedLegLiftPlan::kKp, "kp bound");
                Check(sample.command(joint, 2) == SupportedLegLiftPlan::kKd, "kd bound");
                Check(sample.command(joint, 4) == 0.0f, "feed-forward torque must be zero");
            }
        }
        Check(max_delta <= 0.03, "joint displacement exceeds 0.03 rad");
        Check(max_velocity <= 0.10, "joint target speed exceeds 0.10 rad/s");

        const auto shifted = plan.At(SupportedLegLiftPlan::kShiftSeconds + 0.1);
        Check(shifted.phase == SupportedLegLiftPlan::Phase::HoldShift, "shift hold phase");
        const auto lifted = plan.At(SupportedLegLiftPlan::kShiftSeconds +
            SupportedLegLiftPlan::kShiftHoldSeconds + SupportedLegLiftPlan::kLiftSeconds + 0.1);
        Check(lifted.phase == SupportedLegLiftPlan::Phase::HoldFrontRight, "lift hold phase");
        for (int leg = 0; leg < 4; ++leg) {
            const auto q = Eigen::Vector3d(lifted.command(3 * leg, 1),
                                            lifted.command(3 * leg + 1, 1),
                                            lifted.command(3 * leg + 2, 1));
            const auto shifted_q = plan.shifted()[leg];
            const auto foot = lite3::FootPositionBody(static_cast<lite3::Leg>(leg), q);
            const auto shifted_foot = lite3::FootPositionBody(static_cast<lite3::Leg>(leg), shifted_q);
            const double expected = leg == lite3::LegIndex(lite3::Leg::FR) ?
                SupportedLegLiftPlan::kFootLiftM : 0.0;
            Check(std::abs((foot.z() - shifted_foot.z()) - expected) < 1e-6,
                  "only FR receives the 2 mm Cartesian lift");
        }
        const auto complete = plan.At(SupportedLegLiftPlan::kTotalSeconds + 0.01);
        Check(complete.complete && complete.phase == SupportedLegLiftPlan::Phase::Complete,
              "plan must complete at recentered stand");
        std::cout << "supported leg-lift plan: PASS max_joint_delta=" << max_delta
                  << " max_target_velocity=" << max_velocity << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "supported leg-lift plan: FAIL: " << error.what() << '\n';
        return 1;
    }
}
