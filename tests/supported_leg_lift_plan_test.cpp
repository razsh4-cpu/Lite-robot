#include "state_machine/supported_leg_lift_plan.hpp"

#include <cmath>
#include <iomanip>
#include <iostream>
#include <stdexcept>

namespace {
void Check(bool condition,const char* message) {
    if(!condition)
        throw std::runtime_error(message);
}

double Deg(double r) {
    return r*180.0/M_PI;
}
}

int main() {
    try {
        SupportedLegLiftPlan plan;

        double max_delta=0.0;
        double max_velocity=0.0;

        const int steps =
            static_cast<int>(
                (SupportedLegLiftPlan::kTotalSeconds+0.1)
                /0.001);

        for(int step=0;step<=steps;++step) {
            const double time=step*0.001;
            const auto sample=plan.At(time);

            Check(
                sample.command.allFinite(),
                "all samples must be finite");

            for(int joint=0;joint<12;++joint) {
                const double stand =
                    plan.stand()[joint/3][joint%3];

                max_delta =
                    std::max(
                        max_delta,
                        std::abs(
                            static_cast<double>(
                                sample.command(joint,1))
                            -stand));

                max_velocity =
                    std::max(
                        max_velocity,
                        std::abs(
                            static_cast<double>(
                                sample.command(joint,3))));

                Check(
                    sample.command(joint,0)
                        ==SupportedLegLiftPlan::kKp,
                    "kp bound");

                Check(
                    sample.command(joint,2)
                        ==SupportedLegLiftPlan::kKd,
                    "kd bound");

                Check(
                    sample.command(joint,4)==0.0f,
                    "feed-forward torque must be zero");
            }
        }

        Check(
            max_delta <=
                SupportedLegLiftPlan::kMaxJointDeltaRad,
            "joint displacement exceeds reviewed limit");

        Check(
            max_velocity <=
                SupportedLegLiftPlan::kMaxTargetSpeedRadS,
            "joint target speed exceeds reviewed limit");

        const auto shifted =
            plan.At(
                SupportedLegLiftPlan::kShiftSeconds+
                0.1);

        Check(
            shifted.phase==
                SupportedLegLiftPlan::Phase::HoldShift,
            "shift hold phase");

        const double lift_hold_time =
            SupportedLegLiftPlan::kShiftSeconds+
            SupportedLegLiftPlan::kShiftHoldSeconds+
            SupportedLegLiftPlan::kLiftSeconds+
            0.1;

        const auto lifted =
            plan.At(lift_hold_time);

        Check(
            lifted.phase==
                SupportedLegLiftPlan::Phase::HoldFrontRight,
            "FR lift hold phase");

        std::cout
            << std::fixed
            << std::setprecision(6);

        const char* names[] =
            {"FL","FR","HL","HR"};

        std::cout
            << "\n=== SHIFTED JOINT TARGETS ===\n";

        for(int leg=0;leg<4;++leg) {
            std::cout << names[leg] << ": ";

            for(int joint=0;joint<3;++joint) {
                std::cout
                    << Deg(plan.shifted()[leg][joint]);

                if(joint<2)
                    std::cout << ", ";
            }

            std::cout << " deg\n";
        }

        const int fr =
            lite3::LegIndex(lite3::Leg::FR);

        const auto shifted_xyz =
            lite3::FootPositionBody(
                lite3::Leg::FR,
                plan.shifted()[fr]);

        const auto lifted_xyz =
            lite3::FootPositionBody(
                lite3::Leg::FR,
                plan.lifted()[fr]);

        const auto dp =
            lifted_xyz-shifted_xyz;

        std::cout
            << "\n=== FR LIFT ===\n";

        std::cout
            << "shifted q deg: "
            << Deg(plan.shifted()[fr][0]) << " "
            << Deg(plan.shifted()[fr][1]) << " "
            << Deg(plan.shifted()[fr][2]) << "\n";

        std::cout
            << "lifted q deg:  "
            << Deg(plan.lifted()[fr][0]) << " "
            << Deg(plan.lifted()[fr][1]) << " "
            << Deg(plan.lifted()[fr][2]) << "\n";

        std::cout
            << "FR delta XYZ mm: "
            << dp.x()*1000.0 << " "
            << dp.y()*1000.0 << " "
            << dp.z()*1000.0 << "\n";

        Check(
            std::abs(dp.x()) < 1e-6 &&
            std::abs(dp.y()) < 1e-6 &&
            std::abs(
                dp.z()-
                SupportedLegLiftPlan::kFootLiftM)
                <1e-6,
            "FR Cartesian lift does not match requested 5 mm");

        for(int leg=0;leg<4;++leg) {
            if(leg==fr)
                continue;

            Check(
                (plan.lifted()[leg]-
                 plan.shifted()[leg]).norm()
                    <1e-12,
                "non-FR leg moved during FR curl");
        }

        const auto complete =
            plan.At(
                SupportedLegLiftPlan::kTotalSeconds+
                0.01);

        Check(
            complete.complete &&
            complete.phase==
                SupportedLegLiftPlan::Phase::Complete,
            "plan must finish at stand");

        std::cout
            << "\nPASS"
            << "\nmax_joint_delta="
            << max_delta
            << " rad ("
            << Deg(max_delta)
            << " deg)"
            << "\nmax_target_velocity="
            << max_velocity
            << " rad/s\n";

        return 0;

    } catch(const std::exception& error) {
        std::cerr
            << "supported leg-lift plan: FAIL: "
            << error.what()
            << '\n';

        return 1;
    }
}
