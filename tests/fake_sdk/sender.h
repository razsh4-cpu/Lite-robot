#pragma once
#include "receiver.h"
#include <string>
class Sender {
public:
    Sender(std::string, unsigned short) { ++fake_sdk::sender_constructions; }
    void ControlGet(unsigned mode) {
        if(mode==2) ++fake_sdk::acquisitions;
        if(mode==1) ++fake_sdk::releases;
    }
    void SendCmd(RobotCmd&) { ++fake_sdk::joint_sends; }
    void RobotStateInit() { ++fake_sdk::joint_initializations; }
};
