// Explicit, operator-driven console for staged hardware validation.
// Startup initializes only the existing receive-only feedback path. No SDK
// ownership, posture request, RL request, or velocity is issued automatically.
#include "state_machine.hpp"
#include "stand_signal.hpp"

#include <csignal>
#include <iostream>
#include <sstream>
#include <string>
#include <sys/select.h>
#include <thread>
#include <unistd.h>

using namespace types;

MotionStateFeedback StateBase::msfb_ = MotionStateFeedback();

namespace {
auto& shutdown_requested = stand_signal::requested;
using stand_signal::RequestShutdown;

void PrintStatus(StateMachine& machine) {
    const auto command = machine.VelocitySnapshot();
    const auto q = machine.JointPositionSnapshot();
    std::cout << "STATUS state=" << machine.CurrentMotionState()
              << " state_source=LOCAL_DEPLOY_STATE_MACHINE"
              << " stand_test=" << machine.StandTestStatus()
              << " abort_reason=[" << machine.StandAbortReason() << "]"
              << " preflight=[" << machine.StandPreflightReason() << "]"
              << " acquisition=" << (machine.IsControlRequestSent() ? "REQUEST_SENT" : "NOT_REQUESTED")
              << " ownership=" << machine.OwnershipStatus()
              << " telemetry=" << (machine.TelemetryFresh() ? "FRESH" : "STALE_OR_NEVER_RECEIVED")
              << " feedback_age_s=" << machine.TelemetryAgeSeconds()
              << " joint_send_enabled=" << machine.JointCommandsEnabled()
              << " forward=" << command.forward_vel_scale
              << " lateral=" << command.side_vel_scale
              << " yaw=" << command.turnning_vel_scale << std::endl;
    std::cout << "STATUS q=[";
    for(int joint=0;joint<q.size();++joint) {
        if(joint) std::cout << ',';
        std::cout << q[joint];
    }
    std::cout << "]" << std::endl;
}

void PrintHelp() {
    std::cout << "Commands: status | acquire | authorize_stand SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED | "
                 "stand_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED | "
                 "leg_lift_once SUPPORTED_ESTOP_LEG_TEST_LIMITS_CONFIRMED | "
                 "body_shift_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_30_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_30_reverse_y_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_30_refined_x_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_30_zero_x_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_y5_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_y65_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_x4_y5_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_x2_y5_roll025_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_x2_y5_support05_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_x2_y5_support075_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_physical_c1_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_physical_c2_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_physical_c3_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_physical_pitch_n025_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_physical_pitch_p025_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_physical_height_p05_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_physical_geom_expand_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_physical_force_opt1_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_physical_balanced_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_physical_force_opt2_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_physical_force_opt3_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_physical_large_lean_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_staged_support_triangle_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_60_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "body_shift_90_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED | "
                 "stand | rl_zero_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED | "
                 "forward_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED | "
                 "record_start | record_stop | stop | release | quit. "
                 "Unrestricted RL/velocity blocked; RL_ZERO is limited to 8s then release."
              << std::endl;
}
}  // namespace

int main() {
    std::signal(SIGINT, RequestShutdown);
    std::signal(SIGTERM, RequestShutdown);

    StateMachine machine(RobotType::Lite3);
    std::atomic<bool> worker_failed{false};
    // Lock-free signal latch is checked by worker and private send permit.
    // Handler never performs I/O, releases ownership, or takes a mutex.
    std::thread state_machine_thread([&] {
        try { machine.Run(nullptr, &shutdown_requested); }
        catch (const std::exception& e) {
            std::cerr << "State machine failed: " << e.what() << std::endl;
            worker_failed = true;
        }
        catch (...) { worker_failed = true; }
    });
    std::cout << "PASSIVE validation console started. No SDK control or motion has been requested."
              << std::endl;
    PrintHelp();

    std::string pending;
    try {
    while (shutdown_requested == 0 && !worker_failed.load()) {
        fd_set read_set;
        FD_ZERO(&read_set);
        FD_SET(STDIN_FILENO, &read_set);
        timeval timeout{0, 200000};
        const int ready = select(STDIN_FILENO + 1, &read_set, nullptr, nullptr, &timeout);
        if (pending.find('\n') == std::string::npos) {
            if (ready <= 0) continue;
            char buffer[256];
            const auto count = read(STDIN_FILENO, buffer, sizeof(buffer));
            if (count <= 0) break;
            pending.append(buffer, count);
            if (pending.size() > 4096) {
                machine.StopVelocity(); pending.clear(); continue;
            }
            if (pending.find('\n') == std::string::npos) continue;
        }
        const auto end = pending.find('\n');
        const auto line = pending.substr(0, end);
        pending.erase(0, end+1);
        std::istringstream input(line);
        std::string command;
        input >> command;

        if (command == "record_start") {
            const std::string path =
                std::string("/tmp/lite3-original-pitch-") +
                std::to_string(
                    std::chrono::duration_cast<
                        std::chrono::nanoseconds>(
                            std::chrono::steady_clock::now()
                            .time_since_epoch()).count()) +
                ".jsonl";

            const bool ok =
                machine.StartTelemetryRecording(path);

            std::cout
                << (ok
                    ? "PITCH_RECORDING_ACTIVE "
                    : "PITCH_RECORDING_START_FAILED ")
                << path
                << std::endl;

        } else if (command == "record_stop") {

            const bool ok =
                machine.StopTelemetryRecording();

            std::cout
                << (ok
                    ? "PITCH_RECORDING_STOPPED"
                    : "PITCH_RECORDING_STOP_FAILED")
                << std::endl;
        }

        if (command == "status") {
            PrintStatus(machine);
        } else if (command == "acquire") {
            std::cout << "ACQUIRE BLOCKED: raw ownership handover can drop the vendor posture controller. "
                         "Use only supervised stand/body-shift paths after offline validation."
                      << std::endl;
        } else if (command == "authorize_stand") {
            std::string acknowledgement, extra;
            input >> acknowledgement;
            const bool explicit_ack=acknowledgement=="SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED" && !(input>>extra);
            const bool armed=explicit_ack && machine.AuthorizeStandTest(true,true,true,true);
            std::cout << (armed ? "ARMED for 5s: one supported stand; ownership UNCONFIRMED."
                               : "Authorization rejected. Fresh acquisition, neutral/stable feedback and explicit support/E-stop/health/limits acknowledgment required.")
                      << std::endl;
        } else if (command == "stand_once") {
            std::string acknowledgement, extra;
            input >> acknowledgement;
            bool submitted=false;
            if(!(input>>extra) &&
               acknowledgement=="SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED" &&
               machine.AcquireHardwareControl())
                submitted=machine.RequestStandOnce(acknowledgement);
            std::cout << "STAND_ONCE request " << (submitted ? "submitted" : "blocked")
                      << "; ownership UNCONFIRMED; RL/velocity remain disabled." << std::endl;
        } else if (command == "leg_lift_once") {
        std::string acknowledgement, extra;
        input >> acknowledgement;

        bool submitted=false;

        if(!(input >> extra) &&
           acknowledgement=="SUPPORTED_ESTOP_LEG_TEST_LIMITS_CONFIRMED") {

            const bool acquired=machine.AcquireHardwareControl();

            if(acquired) {
                submitted=
                    machine.RequestSupportedLegLiftOnce(
                        acknowledgement);
            }
        }

        std::cout
            << "LEG_LIFT_ONCE request "
            << (submitted ? "submitted" : "blocked")
            << "; sequence: stand -> shift left/back -> "
               "5mm FR lift -> lower -> recenter."
            << std::endl;

        } else if (command == "body_shift_once" ||
                   command == "body_shift_30_once" ||
                   command == "body_shift_30_reverse_y_once" ||
                   command == "body_shift_30_refined_x_once" ||
                   command == "body_shift_30_zero_x_once" ||
                   command == "body_shift_y5_once" ||
                   command == "body_shift_y65_once" ||
                   command == "body_shift_x4_y5_once" ||
                   command == "body_shift_x2_y5_roll025_once" ||
                   command == "body_shift_x2_y5_support05_once" ||
                   command == "body_shift_x2_y5_support075_once" ||
                   command == "body_shift_physical_c1_once" ||
                   command == "body_shift_physical_c2_once" ||
                   command == "body_shift_physical_c3_once" ||
                   command == "body_shift_physical_pitch_n025_once" ||
                   command == "body_shift_physical_pitch_p025_once" ||
                   command == "body_shift_physical_height_p05_once" ||
                   command == "body_shift_physical_geom_expand_once" ||
                   command == "body_shift_physical_force_opt1_once" ||
                   command == "body_shift_physical_balanced_once" ||
                   command == "body_shift_physical_force_opt2_once" ||
                   command == "body_shift_physical_force_opt3_once" ||
                   command == "body_shift_physical_large_lean_once" ||
                   command == "body_shift_staged_support_triangle_once" ||
                   command == "body_shift_60_once" ||
                   command == "body_shift_90_once") {
            std::string acknowledgement, extra;
            input >> acknowledgement;

            const int level_index=command=="body_shift_30_once" ? 0
                : command=="body_shift_30_reverse_y_once" ? 3
                : command=="body_shift_30_refined_x_once" ? 4
                : command=="body_shift_30_zero_x_once" ? 5
                : command=="body_shift_y5_once" ? 6
                : command=="body_shift_y65_once" ? 7
                : command=="body_shift_x4_y5_once" ? 8
                : command=="body_shift_x2_y5_roll025_once" ? 9
                : command=="body_shift_x2_y5_support05_once" ? 10
                : command=="body_shift_x2_y5_support075_once" ? 11
                : command=="body_shift_physical_c1_once" ? 12
                : command=="body_shift_physical_c2_once" ? 13
                : command=="body_shift_physical_c3_once" ? 14
                : command=="body_shift_physical_pitch_n025_once" ? 15
                : command=="body_shift_physical_pitch_p025_once" ? 16
                : command=="body_shift_physical_height_p05_once" ? 17
                : command=="body_shift_physical_geom_expand_once" ? 18
                : command=="body_shift_physical_force_opt1_once" ? 19
                : command=="body_shift_physical_balanced_once" ? 20
                : command=="body_shift_physical_force_opt2_once" ? 21
                : command=="body_shift_physical_force_opt3_once" ? 22
                : command=="body_shift_physical_large_lean_once" ? 23
                : command=="body_shift_staged_support_triangle_once" ? 24
                : command=="body_shift_60_once" ? 1
                : command=="body_shift_90_once" ? 2 : -1;

            bool submitted=false;

            if(!(input>>extra) &&
               acknowledgement=="SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED") {

                const bool acquired=machine.AcquireHardwareControl();

                if(acquired) {
                    submitted=
                        machine.RequestSupportedBodyShiftOnce(
                            acknowledgement,level_index);
                }
            }

            std::cout << "BODY_SHIFT_ONCE request "
                      << (submitted ? "submitted" : "blocked")
                      << "; body-only "
                      << (level_index<0 ? "30/60/90% sequence"
                          : level_index==0 ? "30%-only"
                          : level_index==3 ? "30%-only reversed-Y"
                          : level_index==4 ? "30%-only refined-X"
                          : level_index==5 ? "30%-only zero-X"
                          : level_index==6 ? "X=-2mm Y=-5mm"
                          : level_index==7 ? "X=-2mm Y=-6.5mm"
                          : level_index==8 ? "X=-4mm Y=-5mm"
                          : level_index==9 ? "X=-2mm Y=-5mm roll-left=0.25deg"
                          : level_index==10 ? "X=-2mm Y=-5mm FL/HR extension=0.5mm"
                          : level_index==11 ? "X=-2mm Y=-5mm FL/HR extension=0.75mm"
                          : level_index==12 ? "physical C1 FL/HR=1.0mm"
                          : level_index==13 ? "physical C2 FL=1.25mm HR=1.0mm"
                          : level_index==14 ? "physical C3 FL/HR=1.25mm"
                          : level_index==15 ? "physical pitch=-0.25deg FL/HR=1.0mm"
                          : level_index==16 ? "physical pitch=+0.25deg FL/HR=1.0mm"
                          : level_index==17 ? "physical height=+0.5mm over C1"
                          : level_index==18 ? "physical coordinated support-triangle expansion"
                          : level_index==19 ? "physical inverse-statics force-opt1"
                          : level_index==20 ? "physical inverse-statics Balanced"
                          : level_index==21 ? "physical structural Force_opt2"
                          : level_index==22 ? "physical combined left/rear tilt identification"
                          : level_index==23 ? "physical large -30mm X/-25mm Y, -2deg roll/pitch lean"
                          : level_index==24 ? "staged FL/HL/HR support-foot placement and X=-14mm hold"
                          : level_index==1 ? "60%-only" : "90%-only")
                      << " calibration, "
                         "stand between levels, automatic release."
                      << std::endl;

            PrintStatus(machine);

        } else if (command == "stand") {
            std::cout << "STAND request " << (machine.RequestStand() ? "submitted" : "blocked")
                      << "; RL/velocity remain disabled." << std::endl;
        } else if (command == "rl_zero_once") {
            std::string acknowledgement, extra;
            input >> acknowledgement;
            const bool accepted=!(input>>extra) && machine.RequestRLZeroOnce(acknowledgement);
            std::cout << "RL_ZERO " << (accepted ? "accepted; normalized velocity locked 0,0,0; 8s maximum then release" : "blocked")
                      << "; ownership UNCONFIRMED. Mechanical support required." << std::endl;
            PrintStatus(machine);
        } else if(command=="forward_once") {
            std::string acknowledgement,extra;input>>acknowledgement;
            const bool accepted=!(input>>extra)&&machine.RequestForwardOnce(acknowledgement);
            std::cout<<"FORWARD_ONCE "<<(accepted?"accepted: 1.0s zero, +0.25 for 1.00s, automatic zero, 5s fallback release":"blocked")
                     <<"; lateral/yaw fixed zero; ownership UNCONFIRMED."<<std::endl;
            PrintStatus(machine);
        } else if (command == "rl" || command == "velocity") {
            machine.StopVelocity();
            std::cout << "BLOCKED: stand-only validation. Test aborted if active." << std::endl;
        } else if (command == "stop") {
            machine.StopVelocity();
            std::cout << "STOP: shared stand-abort/release path; no posture hold promised." << std::endl;
            PrintStatus(machine);
        } else if (command == "release") {
            machine.StopVelocity();
            machine.ReleaseHardwareControl();
            std::cout << "Velocity zeroed; release request sent if pending; ownership return unconfirmed." << std::endl;
            PrintStatus(machine);
        } else if (command == "quit") {
            machine.StopVelocity();
            shutdown_requested = 1;
        } else {
            PrintHelp();
        }
    }
    } catch (const std::exception& e) {
        std::cerr << "Console action failed; stopping: " << e.what() << std::endl;
        worker_failed = true;
    }

    machine.StopVelocity();
    shutdown_requested = 1;
    try { machine.Shutdown(); }
    catch (const std::exception& e) {
        std::cerr << "Release failed; ownership return UNCONFIRMED: " << e.what() << std::endl;
        worker_failed = true;
    }
    state_machine_thread.join();
    return worker_failed.load() ? 1 : 0;
}
