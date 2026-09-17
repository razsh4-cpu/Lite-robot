#include "state_machine.hpp"
#include "../tools/stand_signal.hpp"
#include <algorithm>
#include <atomic>
#include <condition_variable>
#include <future>
#include <iostream>
#include <limits>
#include <stdexcept>
using namespace std::chrono_literals;
MotionStateFeedback StateBase::msfb_ = MotionStateFeedback();
void Check(bool ok,const char* message) { if(!ok) throw std::runtime_error(message); }

struct MockTransport : MotionSdkTransport {
    Feedback callback;
    std::mutex mutex;
    std::condition_variable cv;
    std::vector<std::string> events;
    bool hold_send=false, entered=false, allow_send=false, fail_release=false;
    std::atomic<int> starts{0}, acquires{0}, releases{0}, sends{0};
    void StartFeedback(Feedback f) override { callback=std::move(f); ++starts; }
    void Event(const std::string& event) {
        std::lock_guard<std::mutex> lock(mutex); events.push_back(event);
    }
    void RequestOwnership(unsigned mode) override {
        Check(mode==1 || mode==2,"unexpected SDK operation");
        if(mode==2) { ++acquires; Event("acquire"); }
        else { ++releases; Event("release"); if(fail_release) throw std::runtime_error("inert release failure"); }
    }
    void SendJoints(RobotCmd&) override {
        std::unique_lock<std::mutex> lock(mutex);
        events.push_back("send_begin"); entered=true; cv.notify_all();
        if(hold_send) cv.wait(lock,[&]{return allow_send;});
        ++sends; events.push_back("send_end");
    }
    void Emit(uint32_t tick, bool invalid=false) {
        RobotData d{}; d.tick=tick; d.imu.acc_z=9.81f;
        if(invalid) d.imu.acc_x=std::numeric_limits<float>::quiet_NaN();
        callback(d);
    }
};
// Only the inert test backend can claim confirmed ownership. Production cannot.
struct ConfirmedMockHardware : HardwareInterface {
    using HardwareInterface::HardwareInterface;
    bool IsControlAcquired() const override { return true; }
    const char* OwnershipStatus() const override { return "OWNERSHIP_CONFIRMED"; }
};

void HardwareTests() {
    auto io=std::make_shared<MockTransport>();
    HardwareInterface::Clock::time_point now{};
    HardwareInterface hw("test",io,300ms,[&]{return now;});
    Check(io->starts==0 && io->acquires==0 && io->sends==0,"constructor passive");
    hw.Start(); hw.Start();
    Check(io->starts==1 && io->acquires==0 && io->sends==0,"startup receive only once");
    Check(!hw.AcquireControl(),"no feedback blocks acquire");
    io->Emit(1,true); Check(!hw.IsFeedbackFresh(),"invalid feedback ignored");
    io->Emit(1); Check(hw.IsFeedbackFresh(),"valid feedback fresh");
    Check(hw.AcquireControl() && hw.AcquireControl(),"idempotent acquisition");
    Check(io->acquires==1 && io->sends==0,"acquire only emits ownership request");
    Check(!hw.IsControlAcquired() && hw.IsControlRequestSent(),"request is not confirmation");
    Check(std::string(hw.OwnershipStatus())=="OWNERSHIP_UNCONFIRMED","honest status");
    hw.SetJointCommandEnabled(true); hw.SetJointCommand(MatXf::Zero(12,5));
    Check(!hw.JointCommandsEnabled() && io->sends==0,"unconfirmed ownership blocks sends");
    hw.ReleaseControl(); hw.ReleaseControl();
    Check(io->releases==1,"release idempotent");
    now+=301ms; io->Emit(1);
    Check(!hw.IsFeedbackFresh() && !hw.AcquireControl(),"frozen/stale feedback blocks acquire");
    Check(hw.GetInterfaceTimeStamp()==0.001,"last known telemetry retained");
    io->Emit(2); Check(hw.AcquireControl(),"fresh feedback restores acquire eligibility");
    hw.ReleaseControl();
    Check(io->acquires==2 && io->releases==2,"repeat cycle safe");
    io->Emit(1); now+=301ms; Check(!hw.IsFeedbackFresh(),"backwards tick not fresh");
    std::cout<<"hardware acquisition/freshness tests: PASS\n";
}

void InFlightTest() {
    auto io=std::make_shared<MockTransport>();
    ConfirmedMockHardware hw("test",io,2000ms);
    hw.Start(); io->Emit(1); Check(hw.AcquireControl(),"acquire");
    hw.SetJointCommandEnabled(true);
    io->hold_send=true;
    auto send=std::async(std::launch::async,[&]{hw.SetJointCommand(MatXf::Zero(12,5));});
    {
        std::unique_lock<std::mutex> lock(io->mutex);
        Check(io->cv.wait_for(lock,1s,[&]{return io->entered;}),"send entered");
    }
    auto release=std::async(std::launch::async,[&]{hw.ReleaseControl();});
    Check(release.wait_for(20ms)==std::future_status::timeout,"release must wait for in-flight send");
    { std::lock_guard<std::mutex> lock(io->mutex); io->allow_send=true; }
    io->cv.notify_all(); send.get(); release.get();
    hw.SetJointCommand(MatXf::Zero(12,5));
    Check(io->sends==1 && io->releases==1,"no send after release");
    Check(io->events.back()=="release","release happens last");
    std::cout<<"in-flight send/release serialization: PASS\n";
}

struct ModeState : StateBase {
    StateName mode;
    bool entering_with_gate=false;
    ModeState(std::shared_ptr<ControllerData> d,StateName m)
      : StateBase(Lite3,"mock_mode",d), mode(m) {}
    void OnEnter() override {
        entering_with_gate=ri_ptr_->JointCommandsEnabled();
        msfb_.UpdateCurrentState(static_cast<int>(mode));
        uc_ptr_->SetMotionStateFeedback(msfb_);
    }
    void OnExit() override {}
    void Run() override { ri_ptr_->SetJointCommand(MatXf::Zero(12,5)); }
    bool LoseControlJudge() override { return false; }
    StateName GetNextStateName() override {
        const auto target=uc_ptr_->GetUserCommand().target_mode;
        if(mode==kIdle && target==StandingUp) return kStandUp;
        if(mode==kStandUp && target==RLControlMode) return kRLControl;
        return mode;
    }
};


struct StandFixture {
    double wall=0;
    uint32_t tick=0;
    bool follow=true;
    static HardwareInterface::Clock::time_point Time(double t) {
        return HardwareInterface::Clock::time_point{}+
            std::chrono::duration_cast<HardwareInterface::Clock::duration>(std::chrono::duration<double>(t));
    }
    std::shared_ptr<MockTransport> io=std::make_shared<MockTransport>();
    std::shared_ptr<HardwareInterface> hw=std::make_shared<HardwareInterface>("inert",io,300ms,[this]{return Time(wall);});
    std::shared_ptr<SoftwareVelocityInterface> input=std::make_shared<SoftwareVelocityInterface>();
    std::shared_ptr<ControllerData> data=std::make_shared<ControllerData>();
    std::shared_ptr<ModeState> idle,rl,damping;
    std::shared_ptr<StandUpState> stand;
    std::unique_ptr<StateMachine> machine;
    explicit StandFixture(bool initial_feedback=true) {
        data->ri_ptr=hw; data->uc_ptr=input;
        data->cp_ptr=std::make_shared<ControlParameters>(Lite3);
        idle=std::make_shared<ModeState>(data,kIdle);
        rl=std::make_shared<ModeState>(data,kRLControl);
        damping=std::make_shared<ModeState>(data,kJointDamping);
        stand=std::make_shared<StandUpState>(Lite3,"actual_vendor_stand",data);
        machine=std::make_unique<StateMachine>(hw,input,idle,stand,rl,damping,[this]{return wall;});
        if(initial_feedback) Feedback();
    }
    void Feedback(bool invalid_tilt=false) {
        RobotData d{}; d.tick=++tick*10; d.imu.acc_z=9.81;
        if(invalid_tilt) d.imu.angle_roll=30;
        const auto cmd=hw->GetJointCommand();
        if(follow && io->sends>0) for(int i=0;i<12;++i) d.joint_data.joint_data[i].position=cmd(i,1);
        io->callback(d);
    }
    void Tick() { wall+=.01; Feedback(); machine->ProcessOnce(); }
    void Arm() {
        Check(machine->AcquireHardwareControl(),"acquisition");
        Check(!machine->IsHardwareControlAcquired(),"never fabricate ownership");
        Check(machine->AuthorizeStandTest(true,true,true,true),"explicit stand authorization");
    }
    void Enter() {
        Arm(); Check(machine->RequestStand(),"stand queued");
        Check(!hw->JointCommandsEnabled() && io->sends==0,"pending no sends");
        Tick();
        Check(machine->StandTestStatus()=="STANDING_UP","actual stand entry");
        Check(hw->JointCommandsEnabled() && io->sends==0,"entry precedes gate/no idle send");
    }
};
void StandTests() {
    {
        StandFixture f;
        Check(!f.machine->RequestStand(),"no grant blocks stand");
        f.machine->AcquireHardwareControl();
        Check(!f.machine->AuthorizeStandTest(false,true,true,true),"support required");
        Check(!f.machine->AuthorizeStandTest(true,false,true,true),"E-stop required");
        Check(!f.machine->AuthorizeStandTest(true,true,false,true),"health review required");
        Check(!f.machine->AuthorizeStandTest(true,true,true,false),"limits acceptance required");
        Check(!f.machine->RequestRLControl(),"RL blocked before stand");
        f.machine->AuthorizeStandTest(true,true,true,true);
        Check(!f.machine->AuthorizeStandTest(true,true,true,true),"duplicate grant rejected");
        f.wall=5.01; f.Feedback(); f.machine->ProcessOnce();
        Check(f.io->sends==0 && f.io->releases==1,"expired arm releases without joint sends");
        Check(!f.machine->RequestStand(),"expired token cannot stand");
    }
    for(int reason=0;reason<6;++reason) {
        StandFixture f; f.Enter(); f.Tick();
        Check(f.io->sends>0,"unchanged vendor stand can send through restricted gate");
        const auto sends=f.io->sends.load();
        if(reason==0) f.machine->StopVelocity();
        if(reason==1) f.machine->ReleaseHardwareControl();
        if(reason==2) { f.wall+=.301; f.machine->ProcessOnce(); }
        if(reason==3) f.machine->Shutdown(); // same path used by signals
        if(reason==4) { f.Feedback(true); f.machine->ProcessOnce(); }
        if(reason==5) f.machine->SetVelocityNormalized(.05,0,0);
        Check(f.io->sends==sends,"abort before another Run/send");
        Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),"abort closes/release once");
        Check(f.machine->StandTestStatus()=="RELEASE_REQUESTED","explicit release status");
        Check(f.machine->VelocitySnapshot().forward_vel_scale==0,"velocity remains zero");
        f.machine->ReleaseHardwareControl(); f.machine->Shutdown();
        Check(f.io->releases==1 && f.io->sends==sends,"abort idempotent");
    }
    {
        StandFixture f; f.Enter();
        bool reached=false;
        for(int i=0;i<800 && f.io->releases==0;++i) {
            f.Tick();
            reached |= f.machine->StandTestStatus()=="TARGET_REACHED";
            Check(!f.machine->RequestRLControl(),"RL always blocked during stand");
        }
        Check(reached,"measured convergence reached");
        Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),"successful stand automatically releases");
        Check(f.machine->StandAbortReason()=="stand target hold complete","bounded target hold reason");
    }
    {
        StandFixture f; f.Enter();
        // Feed every packet with a 0.10rad lag: below abort threshold but never converged.
        for(int i=0;i<610 && f.io->releases==0;++i) {
            f.wall+=.01;
            RobotData d{}; d.tick=++f.tick*10; d.imu.acc_z=9.81;
            auto cmd=f.hw->GetJointCommand();
            if(f.io->sends>0) for(int j=0;j<12;++j)
                d.joint_data.joint_data[j].position=cmd(j,1)+(j==0 ? .10f : 0);
            f.io->callback(d); f.machine->ProcessOnce();
        }
        Check(f.io->releases==1,"nonconvergence releases");
        Check(f.machine->StandAbortReason()=="convergence deadline","wall-clock deadline independent of robot ticks");
    }
    {
        StandFixture f; f.Enter(); f.Tick();
        RobotData bad{}; bad.tick=++f.tick*10; bad.imu.acc_z=9.81;
        bad.joint_data.joint_data[0].position=1;
        f.io->callback(bad);
        auto sends=f.io->sends.load(); f.machine->ProcessOnce();
        Check(f.io->releases==1 && f.io->sends==sends,"tracking fault before trajectory");
    }
    {
        StandFixture f; f.Arm(); f.machine->RequestStand(); f.machine->StopVelocity();
        Check(f.io->sends==0 && f.io->releases==1,"pending stop has no joint packet");
        Check(f.machine->AcquireHardwareControl(),"new explicit acquisition");
        Check(!f.machine->RequestStand(),"fresh acquisition cannot reuse grant");
    }
    {
        StandFixture f; f.Enter(); f.Tick();
        const auto sends=f.io->sends.load(); f.io->Emit(++f.tick*10,true);
        f.machine->ProcessOnce();
        Check(f.io->sends==sends && f.io->releases==1,"invalid numeric feedback aborts without freshness grace");
    }
    {
        StandFixture f; f.Enter(); f.Tick(); f.io->fail_release=true;
        bool failed=false;
        try { f.machine->StopVelocity(); } catch(const std::exception&) { failed=true; }
        Check(failed && !f.hw->JointCommandsEnabled(),"release exception stays gate-closed");
        Check(f.machine->StandTestStatus()=="ABORTING" && f.machine->IsControlRequestSent(),"failed release not reported successful");
        f.machine->ReleaseHardwareControl(); f.machine->Shutdown();
        Check(f.io->releases==1,"failed release never retries automatically");
    }
    std::cout<<"supervised actual stand + shared abort + convergence: PASS\n";
}
void SignalLatchTest() {
    for(int sig : {SIGINT,SIGTERM}) {
        StandFixture f;
        f.Enter(); f.Tick();
        const auto sends=f.io->sends.load();
        stand_signal::requested.store(false);
        const auto previous=std::signal(sig,stand_signal::RequestShutdown);
        std::thread worker([&]{f.machine->Run(nullptr,&stand_signal::requested);});
        std::raise(sig); worker.join();
        std::signal(sig,previous);
        Check(!f.machine->AcquireHardwareControl(),"signal shutdown rejects acquisition");
        Check(f.io->sends==sends && f.io->releases==1,"active signal abort before next trajectory");
        Check(!f.hw->JointCommandsEnabled(),"signal closes gate");
    }
}
void StandSendAbortRace() {
    StandFixture f; f.Enter();
    f.io->hold_send=true;
    f.wall+=.01; f.Feedback();
    auto iteration=std::async(std::launch::async,[&]{f.machine->ProcessOnce();});
    {
        std::unique_lock<std::mutex> lock(f.io->mutex);
        Check(f.io->cv.wait_for(lock,1s,[&]{return f.io->entered;}),"stand send entered");
    }
    auto stop=std::async(std::launch::async,[&]{f.machine->StopVelocity();});
    const bool waiting=stop.wait_for(20ms)==std::future_status::timeout;
    const bool not_released=f.io->releases==0;
    { std::lock_guard<std::mutex> lock(f.io->mutex); f.io->allow_send=true; }
    f.io->cv.notify_all(); iteration.get(); stop.get();
    Check(waiting && not_released,"stand abort waits for in-flight send");
    Check(f.io->sends==1 && f.io->releases==1 && f.io->events.back()=="release","release after send completes");
    f.machine->ProcessOnce();
    Check(f.io->sends==1,"no next trajectory after concurrent stop");
}
void StartupTelemetryTest() {
    StandFixture f(false);
    f.machine->ProcessOnce(); f.wall=1; f.machine->ProcessOnce();
    Check(f.machine->StandTestStatus()=="WAITING_FOR_TELEMETRY","startup waits without abort latch");
    Check(f.machine->StandAbortReason().empty(),"startup has no abort reason");
    Check(!f.machine->AcquireHardwareControl() && !f.machine->RequestStand(),"missing feedback blocks control");
    Check(!f.machine->AuthorizeStandTest(true,true,true,true),"missing feedback blocks authorization");
    Check(f.io->acquires==0 && f.io->releases==0 && f.io->sends==0,"startup sends nothing");
    f.io->Emit(1,true); f.machine->ProcessOnce();
    Check(!f.machine->TelemetryFresh(),"invalid first sample cannot unlock startup");
    f.Feedback(); f.Tick();
    Check(f.machine->TelemetryFresh() && f.machine->StandTestStatus()=="LOCKED","fresh advancing feedback exits wait");
    Check(f.machine->StandAbortReason().empty() && !f.hw->JointCommandsEnabled(),"fresh does not authorize output");
    Check(!f.machine->RequestStand() && !f.machine->RequestRLControl(),"fresh alone permits no stand/RL");
    Check(f.machine->VelocitySnapshot().forward_vel_scale==0,"velocity stays zero");
    f.wall+=.301; f.machine->ProcessOnce();
    Check(f.machine->StandTestStatus()=="WAITING_FOR_TELEMETRY","passive telemetry loss waits safely");
    f.Feedback(); f.machine->ProcessOnce();
    Check(f.machine->AcquireHardwareControl(),"existing explicit acquire works after fresh startup");
    Check(!f.machine->IsHardwareControlAcquired(),"ownership remains unconfirmed");
    Check(f.machine->AuthorizeStandTest(true,true,true,true),"explicit arm works without reset/bypass");
    Check(f.io->sends==0 && !f.hw->JointCommandsEnabled(),"arm alone emits no joints");
    f.wall+=.301; f.machine->ProcessOnce();
    Check(f.io->releases==1 && f.machine->StandAbortReason()=="stale telemetry","post-acquire stale still aborts");
    f.Feedback(); f.machine->ProcessOnce();
    Check(f.machine->StandTestStatus()=="RELEASE_REQUESTED" && !f.machine->RequestStand(),"fresh recovery never clears real abort");
    Check(f.io->sends==0,"focused startup test issued no joints even to mock");
    std::cout<<"startup telemetry wait/recovery and acquired-stale latch: PASS\n";
}
int main(int argc, char** argv) {
    try {
        if(argc==2 && std::string(argv[1])=="--startup-only") { StartupTelemetryTest(); return 0; }
        HardwareTests(); InFlightTest(); StandTests(); SignalLatchTest(); StandSendAbortRace();
    }
    catch(const std::exception& e) { std::cerr<<"FAIL: "<<e.what()<<'\n'; return 1; }
    return 0;
}
