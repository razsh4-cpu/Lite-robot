// Production state machine with injected inert transport.
// No physical robot, sockets, or vendor hardware are used by this test.
#define main unused_control_safety_suite_main
#include "control_safety_test.cpp"
#undef main

#include <set>
#include <vector>
#include <fstream>
#include <sstream>

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
            std::vector<std::string> observed_sequence;
            double max_delta=0.0;
            double max_target_velocity=0.0;
            const Eigen::Vector3d stand(
                0.0,-0.7729795255029084,1.5005003509817765);

            const int max_ticks =
                static_cast<int>((SupportedBodyShiftPlan::kTotalSeconds + 10.0) / 0.01);

            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();

                const auto status=f.machine->StandTestStatus();
                seen.insert(status);
                if(status.rfind("BODY_SHIFT_",0)==0 &&
                   (observed_sequence.empty() ||
                    observed_sequence.back()!=status))
                    observed_sequence.push_back(status);

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
                    "BODY_SHIFT_SAFE_30_SETTLE",
                    "BODY_SHIFT_SAFE_30_MOVING",
                    "BODY_SHIFT_SAFE_30_HOLD",
                    "BODY_SHIFT_SAFE_30_RECENTER",
                    "BODY_SHIFT_SAFE_60_SETTLE",
                    "BODY_SHIFT_SAFE_60_MOVING",
                    "BODY_SHIFT_SAFE_60_HOLD",
                    "BODY_SHIFT_SAFE_60_RECENTER",
                    "BODY_SHIFT_SAFE_90_SETTLE",
                    "BODY_SHIFT_SAFE_90_MOVING",
                    "BODY_SHIFT_SAFE_90_HOLD",
                    "BODY_SHIFT_SAFE_90_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"}) {
                Check(seen.count(phase)==1,
                      "every body-shift phase observed");
            }

            const std::vector<std::string> expected_sequence{
                "BODY_SHIFT_SAFE_30_SETTLE", "BODY_SHIFT_SAFE_30_MOVING",
                "BODY_SHIFT_SAFE_30_HOLD", "BODY_SHIFT_SAFE_30_RECENTER",
                "BODY_SHIFT_SAFE_60_SETTLE", "BODY_SHIFT_SAFE_60_MOVING",
                "BODY_SHIFT_SAFE_60_HOLD", "BODY_SHIFT_SAFE_60_RECENTER",
                "BODY_SHIFT_SAFE_90_SETTLE", "BODY_SHIFT_SAFE_90_MOVING",
                "BODY_SHIFT_SAFE_90_HOLD", "BODY_SHIFT_SAFE_90_RECENTER",
                "BODY_SHIFT_VERIFY_STAND"};
            Check(observed_sequence==expected_sequence,
                  "calibration phases occur once in the required order");

            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "completed calibration automatically closes gate and releases");

            Check(f.machine->StandTestStatus()=="RELEASE_REQUESTED",
                  "completed calibration reports release request");

            Check(f.machine->StandAbortReason()=="body shift calibration complete",
                  "completion is distinguished from a safety fault");

            const auto trace_path=f.hw->LastStandTracePath();
            Check(!trace_path.empty(),"completion writes JSONL trace");
            std::ifstream trace_file(trace_path);
            std::ostringstream trace_buffer;
            trace_buffer << trace_file.rdbuf();
            const auto trace=trace_buffer.str();
            for(const char* field : {
                    "\"timestamp_s\"", "\"phase\"", "\"target\"",
                    "\"position\"", "\"velocity\"", "\"torque\"",
                    "\"error\"", "\"world_frame_fz\"",
                    "\"roll\"", "\"pitch\""})
                Check(trace.find(field)!=std::string::npos,
                      "JSONL contains required calibration field");
            for(const char* metadata : {
                    "\"contact_force_source_frame\":\"SDK_FRAME_UNDOCUMENTED\"",
                    "\"contact_force_units\":\"SDK_UNDOCUMENTED\"",
                    "\"contact_force_sign\":\"SDK_UNDOCUMENTED\"",
                    "\"contact_force_order\":\"FL_FR_HL_HR\""})
                Check(trace.find(metadata)!=std::string::npos,
                      "JSONL declares force-channel interpretation limits");
            for(const char* phase : {
                    "BODY_SHIFT_SAFE_30_HOLD", "BODY_SHIFT_SAFE_60_HOLD",
                    "BODY_SHIFT_SAFE_90_HOLD"})
                Check(trace.find(phase)!=std::string::npos,
                      "JSONL contains each calibration hold phase");

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

        for(int level=0;level<3;++level) {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "single-level inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,level),
                  "single-level body-shift action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kLevelSeconds+10.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            const std::string selected=level==0 ? "30" : level==1 ? "60" : "90";
            for(const std::string suffix : {"_SETTLE","_MOVING","_HOLD","_RECENTER"})
                Check(seen.count("BODY_SHIFT_SAFE_"+selected+suffix)==1,
                      "selected single-level phase observed");
            for(const std::string other : {"30","60","90"}) {
                if(other==selected) continue;
                Check(seen.count("BODY_SHIFT_SAFE_"+other+"_MOVING")==0,
                      "unselected calibration level never runs");
            }
            Check(seen.count("BODY_SHIFT_VERIFY_STAND")==1,
                  "single-level action verifies recentered stand");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "single-level action automatically closes gate and releases");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(),
                  "reverse-Y inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,3),
                  "reverse-Y 30-percent action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kLevelSeconds+10.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_SAFE_30_REVERSE_Y_SETTLE",
                    "BODY_SHIFT_SAFE_30_REVERSE_Y_MOVING",
                    "BODY_SHIFT_SAFE_30_REVERSE_Y_HOLD",
                    "BODY_SHIFT_SAFE_30_REVERSE_Y_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1,
                      "every reverse-Y phase observed");
            for(const std::string forbidden : {
                    "BODY_SHIFT_SAFE_30_MOVING",
                    "BODY_SHIFT_SAFE_60_MOVING",
                    "BODY_SHIFT_SAFE_90_MOVING",
                    "LEG_TEST_LIFT_FR"})
                Check(seen.count(forbidden)==0,
                      "reverse-Y action cannot enter another level or lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "reverse-Y action automatically closes gate and releases");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(),
                  "refined-X inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,4),
                  "refined-X action accepted");
            std::set<std::string> seen;
            double verify_started=-1.0;
            bool released_too_early=false;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kLevelSeconds+12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
                if(status=="BODY_SHIFT_VERIFY_STAND" && verify_started<0.0)
                    verify_started=f.wall;
                if(f.io->releases && verify_started>=0.0 &&
                   f.wall-verify_started<SupportedBodyShiftPlan::kVerifyStandSeconds)
                    released_too_early=true;
            }
            for(const std::string phase : {
                    "BODY_SHIFT_SAFE_30_REFINED_X_SETTLE",
                    "BODY_SHIFT_SAFE_30_REFINED_X_MOVING",
                    "BODY_SHIFT_SAFE_30_REFINED_X_HOLD",
                    "BODY_SHIFT_SAFE_30_REFINED_X_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1,
                      "every refined-X phase observed");
            Check(seen.count("LEG_TEST_LIFT_FR")==0,
                  "refined-X action cannot reach lift");
            Check(!released_too_early,
                  "verify stand remains active for the settling interval");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "refined-X action automatically closes gate and releases");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "zero-X inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,5),
                  "zero-X action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kLevelSeconds+12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_SAFE_30_ZERO_X_SETTLE",
                    "BODY_SHIFT_SAFE_30_ZERO_X_MOVING",
                    "BODY_SHIFT_SAFE_30_ZERO_X_HOLD",
                    "BODY_SHIFT_SAFE_30_ZERO_X_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1,
                      "every zero-X phase observed");
            for(const std::string forbidden : {
                    "BODY_SHIFT_SAFE_60_MOVING",
                    "BODY_SHIFT_SAFE_90_MOVING",
                    "LEG_TEST_LIFT_FR"})
                Check(seen.count(forbidden)==0,
                      "zero-X action cannot reach another level or lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "zero-X action automatically closes gate and releases");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "Y5 inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,6),
                  "Y5 action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kLevelSeconds+12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_Y5_SETTLE", "BODY_SHIFT_Y5_MOVING",
                    "BODY_SHIFT_Y5_HOLD", "BODY_SHIFT_Y5_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1, "every Y5 phase observed");
            for(const std::string forbidden : {
                    "BODY_SHIFT_SAFE_60_MOVING",
                    "BODY_SHIFT_SAFE_90_MOVING",
                    "LEG_TEST_LIFT_FR"})
                Check(seen.count(forbidden)==0,
                      "Y5 action cannot reach another level or lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "Y5 action automatically closes gate and releases");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "Y65 inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,7),
                  "Y65 action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kLevelSeconds+12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_Y65_SETTLE", "BODY_SHIFT_Y65_MOVING",
                    "BODY_SHIFT_Y65_HOLD", "BODY_SHIFT_Y65_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1, "every Y65 phase observed");
            for(const std::string forbidden : {
                    "BODY_SHIFT_SAFE_60_MOVING",
                    "BODY_SHIFT_SAFE_90_MOVING",
                    "LEG_TEST_LIFT_FR"})
                Check(seen.count(forbidden)==0,
                      "Y65 action cannot reach another level or lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "Y65 action automatically closes gate and releases");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "X4Y5 inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,8),
                  "X4Y5 action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kLevelSeconds+12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_X4_Y5_SETTLE", "BODY_SHIFT_X4_Y5_MOVING",
                    "BODY_SHIFT_X4_Y5_HOLD", "BODY_SHIFT_X4_Y5_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1, "every X4Y5 phase observed");
            for(const std::string forbidden : {
                    "BODY_SHIFT_SAFE_60_MOVING",
                    "BODY_SHIFT_SAFE_90_MOVING",
                    "LEG_TEST_LIFT_FR"})
                Check(seen.count(forbidden)==0,
                      "X4Y5 action cannot reach another level or lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "X4Y5 action automatically closes gate and releases");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "roll025 inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,9),
                  "roll025 action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kLevelSeconds+12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_X2_Y5_ROLL025_SETTLE",
                    "BODY_SHIFT_X2_Y5_ROLL025_MOVING",
                    "BODY_SHIFT_X2_Y5_ROLL025_HOLD",
                    "BODY_SHIFT_X2_Y5_ROLL025_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1, "every roll025 phase observed");
            for(const std::string forbidden : {
                    "BODY_SHIFT_SAFE_60_MOVING",
                    "BODY_SHIFT_SAFE_90_MOVING",
                    "LEG_TEST_LIFT_FR"})
                Check(seen.count(forbidden)==0,
                      "roll025 action cannot reach another level or lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "roll025 action automatically closes gate and releases");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "support05 inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,10),
                  "support05 action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kLevelSeconds+12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_X2_Y5_SUPPORT05_SETTLE",
                    "BODY_SHIFT_X2_Y5_SUPPORT05_MOVING",
                    "BODY_SHIFT_X2_Y5_SUPPORT05_HOLD",
                    "BODY_SHIFT_X2_Y5_SUPPORT05_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1, "every support05 phase observed");
            for(const std::string forbidden : {
                    "BODY_SHIFT_SAFE_60_MOVING",
                    "BODY_SHIFT_SAFE_90_MOVING",
                    "LEG_TEST_LIFT_FR"})
                Check(seen.count(forbidden)==0,
                      "support05 action cannot reach another level or lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "support05 action automatically closes gate and releases");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "support075 inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,11),
                  "support075 action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kLevelSeconds+12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_X2_Y5_SUPPORT075_SETTLE",
                    "BODY_SHIFT_X2_Y5_SUPPORT075_MOVING",
                    "BODY_SHIFT_X2_Y5_SUPPORT075_HOLD",
                    "BODY_SHIFT_X2_Y5_SUPPORT075_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1, "every support075 phase observed");
            for(const std::string forbidden : {
                    "BODY_SHIFT_SAFE_60_MOVING",
                    "BODY_SHIFT_SAFE_90_MOVING",
                    "LEG_TEST_LIFT_FR"})
                Check(seen.count(forbidden)==0,
                      "support075 action cannot reach another level or lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "support075 action automatically closes gate and releases");
        }

        for(int candidate=0;candidate<3;++candidate) {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(),
                  "physical candidate inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,12+candidate),
                  "physical candidate action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kLevelSeconds+12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            const std::string prefix="BODY_SHIFT_PHYS_C"+
                std::to_string(candidate+1);
            for(const std::string suffix : {
                    "_SETTLE","_MOVING","_HOLD","_RECENTER"})
                Check(seen.count(prefix+suffix)==1,
                      "every physical candidate phase observed");
            Check(seen.count("BODY_SHIFT_VERIFY_STAND")==1,
                  "physical candidate verifies stand");
            for(const std::string forbidden : {
                    "BODY_SHIFT_SAFE_60_MOVING",
                    "BODY_SHIFT_SAFE_90_MOVING",
                    "LEG_TEST_LIFT_FR"})
                Check(seen.count(forbidden)==0,
                      "physical candidate cannot reach another level or lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "physical candidate automatically closes gate and releases");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(),
                  "physical pitch inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,15),
                  "physical pitch action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kLevelSeconds+12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_PHYS_PITCH_N025_SETTLE",
                    "BODY_SHIFT_PHYS_PITCH_N025_MOVING",
                    "BODY_SHIFT_PHYS_PITCH_N025_HOLD",
                    "BODY_SHIFT_PHYS_PITCH_N025_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1,
                      "every physical pitch phase observed");
            for(const std::string forbidden : {
                    "BODY_SHIFT_SAFE_60_MOVING",
                    "BODY_SHIFT_SAFE_90_MOVING",
                    "LEG_TEST_LIFT_FR"})
                Check(seen.count(forbidden)==0,
                      "physical pitch cannot reach another level or lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "physical pitch automatically closes gate and releases");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(),
                  "positive pitch inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,16),
                  "positive pitch action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kLevelSeconds+12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_PHYS_PITCH_P025_SETTLE",
                    "BODY_SHIFT_PHYS_PITCH_P025_MOVING",
                    "BODY_SHIFT_PHYS_PITCH_P025_HOLD",
                    "BODY_SHIFT_PHYS_PITCH_P025_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1,
                      "every positive pitch phase observed");
            Check(seen.count("LEG_TEST_LIFT_FR")==0,
                  "positive pitch cannot reach lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "positive pitch automatically closes gate and releases");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "height inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,17),
                  "height action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kLevelSeconds+12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_PHYS_HEIGHT_P05_SETTLE",
                    "BODY_SHIFT_PHYS_HEIGHT_P05_MOVING",
                    "BODY_SHIFT_PHYS_HEIGHT_P05_HOLD",
                    "BODY_SHIFT_PHYS_HEIGHT_P05_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1,"every height phase observed");
            Check(seen.count("LEG_TEST_LIFT_FR")==0,
                  "height mode cannot reach lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "height mode automatically closes gate and releases");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "geometry inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,18),
                  "geometry action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kLevelSeconds+12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_PHYS_GEOM_EXPAND_SETTLE",
                    "BODY_SHIFT_PHYS_GEOM_EXPAND_MOVING",
                    "BODY_SHIFT_PHYS_GEOM_EXPAND_HOLD",
                    "BODY_SHIFT_PHYS_GEOM_EXPAND_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1,"every geometry phase observed");
            Check(seen.count("LEG_TEST_LIFT_FR")==0,
                  "geometry mode cannot reach lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "geometry mode automatically closes gate and releases");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "force-opt inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,19),
                  "force-opt action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kSettleSeconds+
                 SupportedBodyShiftPlan::kPhysicalForceOptShiftSeconds+
                 SupportedBodyShiftPlan::kHoldSeconds+
                 SupportedBodyShiftPlan::kPhysicalForceOptRecenterSeconds+
                 12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_PHYS_FORCE_OPT1_SETTLE",
                    "BODY_SHIFT_PHYS_FORCE_OPT1_MOVING",
                    "BODY_SHIFT_PHYS_FORCE_OPT1_HOLD",
                    "BODY_SHIFT_PHYS_FORCE_OPT1_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1,"every force-opt phase observed");
            Check(seen.count("LEG_TEST_LIFT_FR")==0,
                  "force-opt cannot reach lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "force-opt automatically closes gate and releases");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "balanced inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,20),
                  "balanced action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kSettleSeconds+
                 SupportedBodyShiftPlan::kPhysicalForceOptShiftSeconds+
                 SupportedBodyShiftPlan::kHoldSeconds+
                 SupportedBodyShiftPlan::kPhysicalForceOptRecenterSeconds+
                 12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_PHYS_BALANCED_SETTLE",
                    "BODY_SHIFT_PHYS_BALANCED_MOVING",
                    "BODY_SHIFT_PHYS_BALANCED_HOLD",
                    "BODY_SHIFT_PHYS_BALANCED_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1,"every balanced phase observed");
            Check(seen.count("LEG_TEST_LIFT_FR")==0,
                  "balanced cannot reach lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "balanced automatically closes gate and releases");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "force-opt2 inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,21),
                  "force-opt2 action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kSettleSeconds+
                 SupportedBodyShiftPlan::kPhysicalForceOpt2ShiftSeconds+
                 SupportedBodyShiftPlan::kHoldSeconds+
                 SupportedBodyShiftPlan::kPhysicalForceOpt2RecenterSeconds+
                 12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_PHYS_FORCE_OPT2_SETTLE",
                    "BODY_SHIFT_PHYS_FORCE_OPT2_MOVING",
                    "BODY_SHIFT_PHYS_FORCE_OPT2_HOLD",
                    "BODY_SHIFT_PHYS_FORCE_OPT2_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1,"every force-opt2 phase observed");
            Check(seen.count("LEG_TEST_LIFT_FR")==0,
                  "force-opt2 cannot reach lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "force-opt2 automatically closes gate and releases");
            Check(f.machine->StandAbortReason()=="body shift calibration complete",
                  "force-opt2 completes without safety abort");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "force-opt3 inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,22),
                  "force-opt3 action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kSettleSeconds+
                 SupportedBodyShiftPlan::kPhysicalForceOpt2ShiftSeconds+
                 SupportedBodyShiftPlan::kHoldSeconds+
                 SupportedBodyShiftPlan::kPhysicalForceOpt2RecenterSeconds+
                 12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_PHYS_FORCE_OPT3_SETTLE",
                    "BODY_SHIFT_PHYS_FORCE_OPT3_MOVING",
                    "BODY_SHIFT_PHYS_FORCE_OPT3_HOLD",
                    "BODY_SHIFT_PHYS_FORCE_OPT3_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1,"every force-opt3 phase observed");
            Check(seen.count("LEG_TEST_LIFT_FR")==0,
                  "force-opt3 cannot reach lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "force-opt3 automatically closes gate and releases");
            Check(f.machine->StandAbortReason()=="body shift calibration complete",
                  "force-opt3 completes without safety abort");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "large-lean inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,23),
                  "large-lean action accepted");
            std::set<std::string> seen;
            const int max_ticks=static_cast<int>(
                (SupportedBodyShiftPlan::kSettleSeconds+
                 SupportedBodyShiftPlan::kPhysicalLargeLeanShiftSeconds+
                 SupportedBodyShiftPlan::kHoldSeconds+
                 SupportedBodyShiftPlan::kPhysicalLargeLeanRecenterSeconds+
                 12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("BODY_SHIFT_",0)==0) seen.insert(status);
            }
            for(const std::string phase : {
                    "BODY_SHIFT_PHYS_LARGE_LEAN_SETTLE",
                    "BODY_SHIFT_PHYS_LARGE_LEAN_MOVING",
                    "BODY_SHIFT_PHYS_LARGE_LEAN_HOLD",
                    "BODY_SHIFT_PHYS_LARGE_LEAN_RECENTER",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1,"every large-lean phase observed");
            Check(seen.count("LEG_TEST_LIFT_FR")==0,
                  "large-lean cannot reach lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "large-lean automatically closes gate and releases");
            Check(f.machine->StandAbortReason()=="body shift calibration complete",
                  "large-lean completes without safety abort");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "staged-stance inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,24),
                  "staged-stance action accepted");
            std::set<std::string> seen;
            const SupportedBodyShiftPlan staged_plan(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                SupportedBodyShiftPlan::RunMode::
                    PhysicalStagedSupportTriangleOnly);
            const int max_ticks=static_cast<int>(
                (staged_plan.total_seconds()+
                 SupportedBodyShiftPlan::kVerifyStandSeconds+12.0)/0.01);
            for(int i=0;i<max_ticks && f.io->releases==0;++i) {
                f.Tick();
                const auto status=f.machine->StandTestStatus();
                if(status.rfind("STANCE_",0)==0 ||
                   status=="BODY_SHIFT_VERIFY_STAND") seen.insert(status);
            }
            for(const std::string phase : {
                    "STANCE_STAGE_SETTLE","STANCE_STAGE_FL_UNLOAD",
                    "STANCE_STAGE_FL_LIFT","STANCE_STAGE_FL_MOVE",
                    "STANCE_STAGE_FL_LOWER","STANCE_STAGE_HL_UNLOAD",
                    "STANCE_STAGE_HL_LIFT","STANCE_STAGE_HL_MOVE",
                    "STANCE_STAGE_HL_LOWER","STANCE_STAGE_HR_UNLOAD",
                    "STANCE_STAGE_HR_LIFT","STANCE_STAGE_HR_MOVE",
                    "STANCE_STAGE_HR_LOWER","STANCE_STAGE_FINAL_SHIFT",
                    "STANCE_STAGE_FINAL_HOLD","STANCE_STAGE_BODY_RECENTER",
                    "STANCE_RESTORE_HR_LIFT","STANCE_RESTORE_HL_LIFT",
                    "STANCE_RESTORE_FL_LIFT","STANCE_STAGE_FINAL_STAND",
                    "BODY_SHIFT_VERIFY_STAND"})
                Check(seen.count(phase)==1,"every key staged-stance phase observed");
            Check(seen.count("LEG_TEST_LIFT_FR")==0,
                  "staged stance never reaches FR lift");
            Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),
                  "staged stance automatically closes gate and releases");
            Check(f.machine->StandAbortReason()=="body shift calibration complete",
                  "staged stance completes without safety abort");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "force-map inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken,0),
                  "force-map 30-percent action accepted");
            while(f.machine->StandTestStatus()!="BODY_SHIFT_SAFE_30_MOVING" &&
                  f.io->releases==0)
                f.Tick();
            RobotData d{};
            d.tick=++f.tick*10;
            d.imu.acc_z=9.81;
            const auto command=f.hw->GetJointCommand();
            for(int i=0;i<12;++i) {
                d.joint_data.joint_data[i].position=command(i,1);
                d.joint_data.joint_data[i].velocity=.001f*i;
                d.joint_data.joint_data[i].torque=.01f*i;
            }
            d.contact_force.fl_leg[2]=11.0;
            d.contact_force.fr_leg[2]=22.0;
            d.contact_force.hl_leg[2]=33.0;
            d.contact_force.hr_leg[2]=44.0;
            f.wall+=.01;
            f.io->callback(d);
            f.machine->ProcessOnce();
            const auto record=f.hw->LastStandRecord();
            const std::array<double,4> expected{{11.0,22.0,33.0,44.0}};
            Check(record.phase=="BODY_SHIFT_SAFE_30_MOVING",
                  "force-map record contains phase");
            for(int leg=0;leg<4;++leg) {
                Check(record.contact_force_z[leg]==expected[leg],
                      "SDK FL/FR/HL/HR z channels preserve order");
                Check(record.world_frame_fz[leg]==expected[leg],
                      "zero-attitude derived world Fz equals raw SDK z");
            }
            Check(record.position[5]==command(5,1) &&
                  std::abs(record.velocity[5]-.005)<1e-7 &&
                  std::abs(record.torque[5]-.05)<1e-7,
                  "actual q/dq/torque are logged from the same feedback packet");
            Check(std::isfinite(record.max_error) && record.roll==0 && record.pitch==0,
                  "tracking error and roll/pitch are logged");
            f.machine->StopVelocity();
            Check(f.io->releases==1,"force-map inert action released after test stop");
        }

        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(), "inert acquire");
            Check(f.machine->RequestSupportedBodyShiftOnce(kToken),
                  "fault run accepted");

            while(f.machine->StandTestStatus()!="BODY_SHIFT_SAFE_30_MOVING" &&
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
