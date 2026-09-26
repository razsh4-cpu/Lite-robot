#include "local_xbox_state_machine.hpp"
#include "idle_state.hpp"
#include "standup_state.hpp"
#include "rl_control_state_onnx.hpp"
#include "joint_damping_state.hpp"
#include "xbox_gamepad_interface.hpp"
#include "hardware/hardware_interface.hpp"
#include "parameters/control_parameters.h"
#include "command_source_arbiter.hpp"
#include "local_xbox_startup_gate.hpp"

#include <cerrno>
#include <csignal>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <linux/joystick.h>
#include <string>
#include <sys/ioctl.h>
#include <unistd.h>

MotionStateFeedback StateBase::msfb_=MotionStateFeedback();

namespace {
volatile std::sig_atomic_t shutdown_requested=0;
void RequestShutdown(int) { shutdown_requested=1; }
void WriteRuntimeState(const char* state) {
    std::ofstream out("/run/lite3-control/LOCAL_XBOX_RUNTIME_STATE",
                      std::ios::trunc);
    if(out) out<<state<<'\n';
}
}

int main() {
    WriteRuntimeState("STARTING");
    constexpr const char* joystick="/dev/input/js0";
    const int fd=open(joystick,O_RDONLY|O_NONBLOCK);
    if(fd<0) {
        WriteRuntimeState("FAULT");
        std::cerr<<"LOCAL_XBOX FAIL_CLOSED: cannot open "<<joystick
                 <<" (errno="<<errno<<"); ownership not requested\n";
        return 2;
    }
    char joystick_name[128]={};
    if(ioctl(fd,JSIOCGNAME(sizeof(joystick_name)),joystick_name)<0 ||
       std::string(joystick_name).find("Xbox")==std::string::npos) {
        WriteRuntimeState("FAULT");
        std::cerr<<"LOCAL_XBOX FAIL_CLOSED: "<<joystick<<" is not an Xbox controller; ownership not requested\n";
        close(fd);
        return 2;
    }
    close(fd);

    CommandSourceLease source_lease;
    LocalXboxStartupGate startup_gate(source_lease);
    if(!startup_gate.Prepare(true)) {
        WriteRuntimeState("BLOCKED");
        std::cerr<<"LOCAL_XBOX FAIL_CLOSED: another command source owns control; ownership not requested\n";
        return 3;
    }
    if(!startup_gate.HardwareConstructionAllowed()) {
        WriteRuntimeState("BLOCKED");
        std::cerr<<"LOCAL_XBOX FAIL_CLOSED: hardware construction gate rejected\n";
        return 3;
    }

    std::signal(SIGINT,RequestShutdown);
    std::signal(SIGTERM,RequestShutdown);

    try {
        auto input=std::make_shared<XboxGamepadInterface>(joystick);
        auto robot=std::make_shared<HardwareInterface>("Lite3");
        auto parameters=std::make_shared<ControlParameters>(RobotType::Lite3);
        auto streaming=std::make_shared<DataStreaming>(false,false);
        auto data=std::make_shared<ControllerData>();
        data->ri_ptr=robot;
        data->uc_ptr=input;
        data->cp_ptr=parameters;
        data->ds_ptr=streaming;

        auto idle=std::make_shared<IdleState>(RobotType::Lite3,"idle_state",data);
        auto stand=std::make_shared<StandUpState>(RobotType::Lite3,"standup_state",data);
        auto rl=std::make_shared<RLControlStateONNX>(RobotType::Lite3,"rl_control",data);
        auto damping=std::make_shared<JointDampingState>(RobotType::Lite3,"joint_damping",data);

        LocalXboxStateMachine runtime(robot,input,idle,stand,rl,damping);
        WriteRuntimeState("Idle / WaitingForStand");
        runtime.Run(&shutdown_requested);
    } catch(const std::exception& e) {
        WriteRuntimeState("FAULT");
        std::cerr<<"LOCAL_XBOX stopped: "<<e.what()<<'\n';
        return 1;
    }
    WriteRuntimeState("STOPPED");
    return 0;
}
