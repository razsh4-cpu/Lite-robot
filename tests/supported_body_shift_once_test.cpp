// Production state machine with injected inert transport.
// No physical robot, sockets, or vendor hardware are used by this test.
#define main unused_control_safety_suite_main
#include "control_safety_test.cpp"
#undef main

#include <set>

namespace {
constexpr const char* kToken="SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED";
}

int main() {
    try {
        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "inert acquire");
            Check(!f.machine->RequestSupportedBodyShiftOnce(""),
                  "missing token rejected");
            Check(!f.machine->RequestSupportedBodyShiftOnce(
                      "SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED"),
                  "stand token rejected");
            Check(f.io->sends==0 && !f.hw->JointCommandsEnabled(),
                  "rejected request cannot send");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken),
                  "body-shift action accepted");
            Check(f.machine->StandTestStatus()=="PENDING",
                  "action starts pending");

            std::set<std::string> seen;
            double max_delta=0.0;
            double max_target_velocity=0.0;
            const Eigen::Vector3d stand(
                0.0,-0.7729795255029084,1.5005003509817765);

            for(int i=0;i<1600 && f.io->releases==0;++i) {
                f.Tick();

                const auto status=f.machine->StandTestStatus();
                seen.insert(status);

                const auto command=f.hw->GetJointCommand();

                if(status.rfind("BODY_SHIFT_",0)==0) {
                    for(int joint=0;joint<12;++joint) {
                        max_delta=std::max(
                            max_delta,
                            std::abs(
                                static_cast<double>(command(joint,1)) -
                                stand[joint%3]));

                        max_target_velocity=std::max(
                            max_target_velocity,
                            std::abs(
                                static_cast<double>(command(joint,3))));

                        Check(command(joint,4)==0,
                              "feed-forward torque remains zero");
                        Check(command(joint,0)<=100.0001f,
                              "kp stays inside reviewed bound");
                        Check(command(joint,2)<=2.5001f,
                              "kd stays inside reviewed bound");
                    }
                }
            }

            for(const char* phase : {
                    "BODY_SHIFT_SHIFT_WEIGHT",
                    "BODY_SHIFT_HOLD",
                    "BODY_SHIFT_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"}) {
                Check(seen.count(phase)==1,
                      "every body-shift phase observed");
            }

            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "completed action closes gate and releases once");

            Check(f.machine->StandAbortReason()=="supported body shift complete",
                  "successful completion reason");

            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad && max_target_velocity<=0.10,
                  "trajectory remains inside reviewed limits");

            Check(!f.machine->RequestSupportedBodyShiftOnce(kToken),
                  "one acquisition cannot repeat action");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken),
                  "fault run accepted");

            while(f.machine->StandTestStatus()!="BODY_SHIFT_SHIFT_WEIGHT" &&
                  f.io->releases==0)
                f.Tick();

            Check(f.io->releases==0, "test entered shift phase");

            const auto sends=f.io->sends.load();

            // Existing fixture fault injection used by the leg-lift test.
            f.wall+=.01;
            f.Feedback(true);
            f.machine->ProcessOnce();

            Check(f.io->releases==1 && f.io->sends==sends,
                  "tilt fault aborts before another send");

            Check(!f.hw->JointCommandsEnabled(),
                  "tilt fault closes gate");
        }

        std::cout << "supported body-shift once inert tests: PASS\n";
        return 0;

    } catch(const std::exception& error) {
        std::cerr << "supported body-shift once test: FAIL: "
                  << error.what() << '\n';
        return 1;
    }
}
