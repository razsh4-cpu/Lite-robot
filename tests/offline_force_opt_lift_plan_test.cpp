#include "tools/offline_force_opt_lift_plan.hpp"

#include <cmath>
#include <iomanip>
#include <iostream>
#include <stdexcept>

namespace {
void Check(bool condition,const char* message) {
    if(!condition) throw std::runtime_error(message);
}

void PrintPose(const char* label,const OfflineForceOptLiftPlan::Pose& pose) {
    std::cout << label << " q=[";
    for(int leg=0;leg<4;++leg)
        for(int joint=0;joint<3;++joint) {
            if(leg || joint) std::cout << ',';
            std::cout << pose[leg][joint];
        }
    std::cout << "]\n";
}
}

int main() {
    try {
        OfflineForceOptLiftPlan plan;
        const int fr=lite3::LegIndex(lite3::Leg::FR);
        const auto support_xyz=lite3::FootPositionBody(
            lite3::Leg::FR,plan.support()[fr]);
        const auto lift2_xyz=lite3::FootPositionBody(
            lite3::Leg::FR,plan.lift2()[fr]);
        const auto lift3_xyz=lite3::FootPositionBody(
            lite3::Leg::FR,plan.lift3()[fr]);

        Check((lift2_xyz-support_xyz-Eigen::Vector3d(0,0,0.002)).norm()<5e-6,
              "2 mm Cartesian lift mismatch");
        Check((lift3_xyz-support_xyz-Eigen::Vector3d(0,0,0.003)).norm()<5e-6,
              "3 mm Cartesian lift mismatch");
        for(int leg=0;leg<4;++leg) {
            if(leg==fr) continue;
            Check((plan.lift2()[leg]-plan.support()[leg]).norm()<1e-12,
                  "2 mm lift moved a support leg");
            Check((plan.lift3()[leg]-plan.support()[leg]).norm()<1e-12,
                  "3 mm lift moved a support leg");
        }
        Check(plan.WithinReviewedEnvelope(plan.lift2()),
              "2 mm lift must fit reviewed envelope");
        Check(!plan.WithinReviewedEnvelope(plan.lift3()),
              "3 mm lift must remain rejected at the 0.03 rad limit");

        std::cout << std::fixed << std::setprecision(12);
        PrintPose("support",plan.support());
        PrintPose("lift2",plan.lift2());
        PrintPose("lift3",plan.lift3());
        std::cout << "lift2 max_delta="
                  << OfflineForceOptLiftPlan::MaxJointDeltaFromStand(plan.lift2())
                  << " max_speed=" << plan.MaxTargetSpeed(plan.lift2()) << '\n';
        std::cout << "lift3 max_delta="
                  << OfflineForceOptLiftPlan::MaxJointDeltaFromStand(plan.lift3())
                  << " max_speed=" << plan.MaxTargetSpeed(plan.lift3()) << '\n';
        std::cout << "offline force-opt lift plan: PASS\n";
        return 0;
    } catch(const std::exception& error) {
        std::cerr << "offline force-opt lift plan: FAIL: " << error.what() << '\n';
        return 1;
    }
}
