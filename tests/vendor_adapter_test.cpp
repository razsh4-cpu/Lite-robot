#include "hardware/hardware_interface.hpp"
#include "receiver.h"
#include <iostream>
#include <stdexcept>
void Check(bool value,const char* reason) { if(!value) throw std::runtime_error(reason); }
int main() {
    using namespace fake_sdk;
    try {
        HardwareInterface hw("inert adapter");
        Check(sender_constructions==0 && receiver_constructions==0,"constructor must not create SDK objects");
        hw.Start(); hw.Start();
        Check(receiver_constructions==1 && start_calls==1,"receiver must start only once");
        Check(sender_constructions==0 && acquisitions==0 && joint_sends==0 && joint_initializations==0,
              "passive startup emitted command");
        Check(!hw.AcquireControl(),"no telemetry blocks acquisition");
        Receiver::instance->Emit(1);
        Check(hw.AcquireControl() && hw.AcquireControl(),"acquisition request");
        Check(sender_constructions==1 && acquisitions==1,"exactly one acquisition");
        Check(joint_initializations==0 && joint_sends==0,"acquire-only called init or send");
        hw.SetJointCommandEnabled(true);
        hw.SetJointCommand(MatXf::Zero(12,5));
        Check(joint_sends==0,"unconfirmed ownership allowed joint streaming");
        hw.ReleaseControl(); hw.ReleaseControl();
        Check(releases==1 && joint_sends==0,"release must be idempotent");
        std::cout<<"production adapter with inert SDK symbols: PASS\n";
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; return 1; }
}
