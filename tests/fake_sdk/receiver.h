#pragma once
#include "robot_types.h"
#include <functional>
namespace fake_sdk {
inline int receiver_constructions=0, start_calls=0, sender_constructions=0;
inline int acquisitions=0, releases=0, joint_sends=0, joint_initializations=0;
}
class Receiver {
    RobotData state_{};
    std::function<void(int)> callback_;
public:
    inline static Receiver* instance=nullptr;
    Receiver() { instance=this; ++fake_sdk::receiver_constructions; StartWork(); }
    void StartWork() { ++fake_sdk::start_calls; }
    void RegisterCallBack(std::function<void(int)> callback) { callback_=std::move(callback); }
    RobotData& GetState() { return state_; }
    void Emit(uint32_t tick) { state_.tick=tick; state_.imu.acc_z=9.81f; callback_(0x0906); }
    void SetFootForceZ(double fl, double fr, double hl, double hr) {
        state_.contact_force.fl_leg[2]=fl;
        state_.contact_force.fr_leg[2]=fr;
        state_.contact_force.hl_leg[2]=hl;
        state_.contact_force.hr_leg[2]=hr;
    }
};
