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

            Check(!f.machine->RequestSupportedBodyShiftSafeOnce(""),
                  "safe combined path rejects missing acknowledgement");
            Check(f.io->sends==0,
                  "rejected safe combined request cannot send");

            Check(f.machine->RequestSupportedBodyShiftSafeOnce(kToken),
                  "safe combined body-shift accepted");

            Check(f.machine->StandTestStatus()=="STANDING_UP",
                  "safe combined path enters stand immediately");

            Check(f.hw->JointCommandsEnabled(),
                  "safe combined path opens supervised stand gate");

            Check(f.io->sends>=1,
                  "safe combined handover sends first stand command immediately");

            const auto first=f.hw->GetJointCommand();

            Check(first.rows()==12 && first.cols()==5 && first.allFinite(),
                  "first handover stand command is finite");

            for(int i=0;i<12;++i) {
                Check(first(i,0)>=0 && first(i,0)<=100.0001f,
                      "first command kp bounded");
                Check(first(i,2)>=0 && first(i,2)<=2.5001f,
                      "first command kd bounded");
                Check(first(i,4)==0.0f,
                      "first command feed-forward torque zero");
            }
        }

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

            const int max_ticks =
                static_cast<int>((SupportedBodyShiftPlan::kTotalSeconds + 5.0) / 0.01);

            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
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

            Check(f.io->releases==0 && f.hw->JointCommandsEnabled(),
                  "completed body shift keeps supervised stand gate open");

            Check(f.machine->StandTestStatus()=="BODY_SHIFT_HOLD_STAND",
                  "completed body shift remains standing under code control");

            std::cerr << "BODY_SHIFT_MEASURED max_delta=" << max_delta
                      << " limit=" << SupportedBodyShiftPlan::kMaxJointDeltaRad
                      << " max_target_velocity=" << max_target_velocity
                      << " velocity_limit=0.10" << std::endl;
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad &&
                  max_target_velocity<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS,
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
