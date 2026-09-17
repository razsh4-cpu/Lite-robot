// Production state machine with injected inert SDK transport. No sockets or
// vendor hardware objects are linked into this test.
#define main unused_control_safety_suite_main
#include "control_safety_test.cpp"
#undef main

#include <set>

namespace {
constexpr const char* kToken="SUPPORTED_ESTOP_LEG_TEST_LIMITS_CONFIRMED";
}

int main() {
    try {
        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "inert acquire");
            Check(!f.machine->RequestSupportedLegLiftOnce(""), "missing token rejected");
            Check(!f.machine->RequestSupportedLegLiftOnce(
                "SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED"), "stand token rejected");
            Check(f.io->sends==0 && !f.hw->JointCommandsEnabled(),
                  "rejected request cannot send");
        }
        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "inert acquire");
            Check(f.machine->RequestSupportedLegLiftOnce(kToken), "leg action accepted");
            Check(f.machine->StandTestStatus()=="PENDING", "action starts pending");
            std::set<std::string> seen;
            double max_delta=0.0, max_target_velocity=0.0;
            const Eigen::Vector3d stand(0.0,-0.7729795255029084,1.5005003509817765);
            for(int i=0;i<1500 && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                seen.insert(status);
                const auto command=f.hw->GetJointCommand();
                if(status.rfind("LEG_TEST_",0)==0) for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,
                        std::abs(static_cast<double>(command(joint,1))-stand[joint%3]));
                    max_target_velocity=std::max(max_target_velocity,
                        std::abs(static_cast<double>(command(joint,3))));
                    Check(command(joint,4)==0, "feed-forward torque remains zero");
                }
            }
            for(const char* phase : {"LEG_TEST_SHIFT_BODY","LEG_TEST_HOLD_SHIFT",
                    "LEG_TEST_LIFT_FR","LEG_TEST_HOLD_FR","LEG_TEST_LOWER_FR",
                    "LEG_TEST_RECENTER","LEG_TEST_VERIFY_STAND"})
                Check(seen.count(phase)==1, "every bounded phase observed");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "completed action closes gate and releases once");
            Check(f.machine->StandAbortReason()=="supported leg lift complete",
                  "successful completion reason");
            Check(max_delta<=0.03 && max_target_velocity<=0.10,
                  "trajectory remains inside reviewed limits");
            Check(!f.machine->RequestSupportedLegLiftOnce(kToken),
                  "one acquisition cannot repeat action");
        }
        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "inert acquire");
            Check(f.machine->RequestSupportedLegLiftOnce(kToken), "fault run accepted");
            while(f.machine->StandTestStatus()!="LEG_TEST_SHIFT_BODY" && f.io->releases==0)
                f.Tick();
            Check(f.io->releases==0, "test entered shift phase");
            const auto sends=f.io->sends.load();
            f.wall+=.01; f.Feedback(true); f.machine->ProcessOnce();
            Check(f.io->releases==1 && f.io->sends==sends,
                  "tilt fault aborts before another send");
            Check(!f.hw->JointCommandsEnabled(), "tilt fault closes gate");
        }
        std::cout << "supported leg-lift once inert tests: PASS\n";
        return 0;
    } catch(const std::exception& error) {
        std::cerr << "supported leg-lift once test: FAIL: " << error.what() << '\n';
        return 1;
    }
}
