// Receive-only readiness tool. This translation unit never includes Sender.
// Any accidental control API call throws before doing anything.
#include "hardware/hardware_interface.hpp"
#include "receiver.h"
#include <atomic>
#include <fstream>
#include <iostream>
#include <thread>
#include <cstdlib>
class ReceiveOnly final : public MotionSdkTransport {
public:
    std::atomic<uint64_t> packets{0};
    void StartFeedback(Feedback callback) override {
        auto* receiver=new Receiver(); // vendor detached receiver lives until process exit
        receiver->RegisterCallBack([this,receiver,callback](int code) {
            if(code==0x0906) { callback(receiver->GetState()); ++packets; }
        });
    }
    void RequestOwnership(unsigned) override { throw std::logic_error("PASSIVE ONLY: ownership forbidden"); }
    void SendJoints(RobotCmd&) override { throw std::logic_error("PASSIVE ONLY: sending forbidden"); }
};
int main() {
    auto io=std::make_shared<ReceiveOnly>();
    auto hw=std::make_shared<HardwareInterface>("passive observer",io);
    hw->Start();
    std::ofstream log("/tmp/lite3-stand-passive-observation.csv");
    log<<"wall_s,tick_s,age_s,fresh,roll,pitch";
    for(int i=0;i<12;++i) log<<",q"<<i<<",dq"<<i<<",tau"<<i;
    log<<'\n'; log.precision(12);
    auto start=HardwareInterface::Clock::now();
    uint64_t fresh=0, stale=0, progressing=0; double last=-1,max_age=0;
    std::array<double,12> low,high,jump{},previous{};
    low.fill(INFINITY); high.fill(-INFINITY);
    for(int n=0;n<3500;++n) {
        auto s=hw->GetStandFeedback();
        const auto wall=std::chrono::duration<double>(HardwareInterface::Clock::now()-start).count();
        if(s.fresh) {
            ++fresh; max_age=std::max(max_age,s.age);
            if(s.stamp!=last) {
                ++progressing;
                for(int i=0;i<12;++i) {
                    low[i]=std::min(low[i],double(s.q[i])); high[i]=std::max(high[i],double(s.q[i]));
                    if(last>=0) jump[i]=std::max(jump[i],std::abs(double(s.q[i])-previous[i]));
                    previous[i]=s.q[i];
                } last=s.stamp;
            }
        } else ++stale;
        log<<wall<<','<<s.stamp<<','<<s.age<<','<<s.fresh<<','<<s.rpy[0]<<','<<s.rpy[1];
        for(int i=0;i<12;++i) log<<','<<s.q[i]<<','<<s.dq[i]<<','<<s.torque[i];
        log<<'\n';
        std::this_thread::sleep_until(start+std::chrono::milliseconds((n+1)*10));
    }
    const auto seconds=std::chrono::duration<double>(HardwareInterface::Clock::now()-start).count();
    std::cout<<"PASSIVE packets="<<io->packets<<" seconds="<<seconds<<" callback_hz="<<io->packets/seconds
        <<" fresh_samples="<<fresh<<" stale_or_startup_samples="<<stale<<" progressing_samples="<<progressing
        <<" max_fresh_age_s="<<max_age<<" gate="<<hw->JointCommandsEnabled()
        <<" request="<<hw->IsControlRequestSent()<<" ownership="<<hw->OwnershipStatus()<<'\n';
    for(int i=0;i<12;++i) std::cout<<"JOINT "<<i<<' '<<stand_diagnostics::Leg(i)<<' '<<stand_diagnostics::Joint(i)
        <<" min="<<low[i]<<" max="<<high[i]<<" max_sample_delta="<<jump[i]<<'\n';
    log.flush(); std::cout.flush();
    // Vendor receiver has no stop/join API. End this receive-only process without
    // destroying callback captures while its detached thread can still run.
    std::_Exit(fresh>0?0:2);
}
