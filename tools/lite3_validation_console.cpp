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
}

void PrintHelp() {
    std::cout << "Commands: status | acquire | authorize_stand SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED | "
                 "stand_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED | "
                 "stand | rl_zero_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED | "
                 "forward_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED | stop | release | quit. "
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

        if (command == "status") {
            PrintStatus(machine);
        } else if (command == "acquire") {
            // This is an explicit operator action. Motion remains zero.
            const bool requested = machine.AcquireHardwareControl();
            std::cout << "ACQUIRE request " << (requested ? "submitted" : "failed")
                      << "; MotionSDK exposes no ownership acknowledgement. "
                         "Verify robot posture and telemetry before the next action."
                      << std::endl;
            PrintStatus(machine);
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
            const bool submitted=!(input>>extra) && machine.RequestStandOnce(acknowledgement);
            std::cout << "STAND_ONCE request " << (submitted ? "submitted" : "blocked")
                      << "; ownership UNCONFIRMED; RL/velocity remain disabled." << std::endl;
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
