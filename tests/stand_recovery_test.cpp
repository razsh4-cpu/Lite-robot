// Inert-only replay: reuses the existing injected mock transport/fixtures.
// NO vendor library, sockets, policy execution, or hardware constructor linked.
#define main existing_control_safety_suite_main
#include "control_safety_test.cpp"
#undef main
#include <fstream>
#include <iomanip>

static const std::array<float,12> recorded_q={.0669479,.41935,2.73736,-.0818253,.339699,2.39868,
    .0785446,-.0981522,2.40273,-.0762558,-.187416,2.67723};
static const std::array<float,12> recorded_dq={.00904083,.050087,-.0210953,-.00278473,.00293732,.00164032,
    .0140762,.0792313,.0205612,.0492477,.0181198,-.0201035};
struct CapturingTransport : MockTransport {
    RobotCmd last{};
    bool fail_send=false;
    void SendJoints(RobotCmd& cmd) override {
        if(fail_send) throw std::runtime_error("inert send failure");
        last=cmd; MockTransport::SendJoints(cmd);
    }
};

struct Replay {
    double wall=0; uint32_t tick=1000;
    std::shared_ptr<CapturingTransport> io=std::make_shared<CapturingTransport>();
    std::shared_ptr<HardwareInterface> hw=std::make_shared<HardwareInterface>("replay",io,300ms,[this]{return StandFixture::Time(wall);});
    std::shared_ptr<SoftwareVelocityInterface> input=std::make_shared<SoftwareVelocityInterface>();
    std::shared_ptr<ControllerData> data=std::make_shared<ControllerData>();
    std::shared_ptr<IdleState> idle;
    std::shared_ptr<StandUpState> stand;
    std::shared_ptr<ModeState> rl,damping;
    std::unique_ptr<StateMachine> sm;
    RobotData measured{};
    Replay(uint32_t base=1000, const std::array<float,12>& initial=recorded_q) : tick(base) {
        data->ri_ptr=hw; data->uc_ptr=input; data->cp_ptr=std::make_shared<ControlParameters>(Lite3);
        idle=std::make_shared<IdleState>(Lite3,"real_idle",data);
        stand=std::make_shared<StandUpState>(Lite3,"real_stand",data);
        rl=std::make_shared<ModeState>(data,kRLControl); damping=std::make_shared<ModeState>(data,kJointDamping);
        sm=std::make_unique<StateMachine>(hw,input,idle,stand,rl,damping,[this]{return wall;},data->cp_ptr);
        measured.imu.acc_z=9.81;
        for(int i=0;i<12;++i) {measured.joint_data.joint_data[i].position=initial[i]; measured.joint_data.joint_data[i].velocity=recorded_dq[i];}
        Emit();
    }
    void Emit() {measured.tick=++tick; io->callback(measured);}
    void Enter(double delay=0) {
        Check(sm->AcquireHardwareControl(),"replay inert acquire");
        Check(sm->AuthorizeStandTest(true,true,true,true),"replay authorize");
        wall+=delay; Emit(); Check(sm->RequestStand(),"replay request");
        Check(io->sends==0 && !hw->JointCommandsEnabled(),"request does not send");
        // Real IdleState has an entry settle interval; progress robot time before requesting transition.
        tick+=2001; Emit(); sm->ProcessOnce();
        Check(sm->StandTestStatus()=="STANDING_UP","real Idle permits recorded posture");
        Check(io->sends==0 && hw->JointCommandsEnabled(),"entry before first send");
    }
};

void FullReplay(uint32_t uptime, double arm_delay, bool frozen=false, const std::array<float,12>& initial=recorded_q) {
    Replay f(uptime,initial); f.Enter(arm_delay);
    // Exact entry command: must equal measured q/dq, no fixed starting jump.
    f.stand->Run();
    auto previous=f.hw->GetJointCommand();
    for(int j=0;j<12;++j) {
        Check(std::abs(previous(j,1)-initial[j])<1e-6,"initial q captured");
        Check(std::abs(previous(j,3)-recorded_dq[j])<1e-6,"initial dq captured");
    }
    double max_delta=0, max_speed=0, max_accel=0;
    bool reached=false, phase1=false, phase2=false;
    for(int n=1;n<=5600 && f.io->releases==0;++n) {
        f.wall+=.001;
        if(!frozen) for(int j=0;j<12;++j) {
            f.measured.joint_data.joint_data[j].position=previous(j,1);
            f.measured.joint_data.joint_data[j].velocity=previous(j,3);
        }
        f.Emit(); f.sm->ProcessOnce();
        if(f.io->releases) break;
        auto current=f.hw->GetJointCommand();
        for(int j=0;j<12;++j) {
            max_delta=std::max(max_delta,double(std::abs(current(j,1)-previous(j,1))));
            max_speed=std::max(max_speed,double(std::abs(current(j,3))));
            max_accel=std::max(max_accel,double(std::abs(current(j,3)-previous(j,3))/.001));
            Check(current(j,0)==100 && current(j,2)==2.5 && current(j,4)==0,"gains/ff unchanged");
            const auto& packet=f.io->last.joint_cmd[j];
            Check(packet.position==current(j,1) && packet.velocity==current(j,3) &&
                  packet.kp==100 && packet.kd==2.5 && packet.torque==0,"all 12 SDK command fields map identically");
            Check(current(j,1)>=f.data->cp_ptr->fl_joint_lower_[j%3]-.1 &&
                  current(j,1)<=f.data->cp_ptr->fl_joint_upper_[j%3]+.1,"trajectory software position bounds");
            Check(std::abs(current(j,3))<=f.data->cp_ptr->joint_vel_limit_[j%3],"velocity bounds");
        }
        if(n==1500) {
            for(int leg=0;leg<4;++leg) {
                Check(std::abs(current(leg*3+1,1)+1.354531)<2e-5,"pre target");
                Check(std::abs(current(leg*3+2,1)-2.549477)<2e-5,"pre knee");
            } phase1=true;
        }
        if(n>=3001) {
            for(int leg=0;leg<4;++leg) {
                Check(std::abs(current(leg*3,1))<1e-6,"final HipX");
                Check(std::abs(current(leg*3+1,1)+.772979526)<2e-5,"final HipY");
                Check(std::abs(current(leg*3+2,1)-1.50050035)<2e-5,"final knee");
            } phase2=true;
        }
        Check(!f.sm->RequestRLControl(),"RL blocked throughout");
        reached |= f.sm->StandTestStatus()=="TARGET_REACHED";
        previous=current;
    }
    if(frozen) {
        Check(f.io->releases==1,"frozen physical response aborts");
        Check(f.sm->StandAbortReason().find("TRACKING_ERROR")!=std::string::npos ||
              f.sm->StandAbortReason()=="tracking error","frozen response tracking reason");
    } else {
        Check(phase1 && phase2 && reached,"full real trajectory plus measured convergence");
        Check(f.io->releases==1 && !f.hw->JointCommandsEnabled(),"successful stand automatically releases");
        Check(f.sm->StandAbortReason()=="stand target hold complete","bounded target hold release");
        Check(max_delta<.004,"no phase/uptime position discontinuity");
    }
    Check(!f.hw->JointCommandsEnabled() && f.io->releases==1,"final closed gate/release");
    std::cout<<"REPLAY uptime_ms="<<uptime<<" arm_delay="<<arm_delay<<" frozen="<<frozen
        <<" sends="<<f.io->sends<<" max_delta="<<max_delta<<" max_speed="<<max_speed
        <<" max_accel="<<max_accel<<" result="<<f.sm->StandAbortReason()<<'\n';
}

void GuardReasons() {
    using R=stand_diagnostics::Reason;
    for(int which=0;which<8;++which) {
        Replay f; f.Enter();
        f.stand->Run(); auto cmd=f.hw->GetJointCommand();
        R expected=R::OTHER;
        if(which==0) {cmd(4,1)+=.36; expected=R::TRACKING_ERROR;}
        if(which==1) {cmd(2,1)=std::numeric_limits<float>::quiet_NaN();expected=R::INVALID_COMMAND;}
        if(which==2) {f.wall+=.301;expected=R::STALE_FEEDBACK;}
        if(which==3) {f.measured.imu.angle_roll=30;f.Emit();expected=R::EXCESSIVE_TILT;}
        if(which==4) {f.measured.joint_data.joint_data[10].position=std::numeric_limits<float>::infinity();f.Emit();expected=R::INVALID_MEASURED_STATE;}
        if(which==5) {cmd(2,4)=1;expected=R::INVALID_COMMAND;}
        if(which==6) {f.io->fail_send=true;expected=R::OTHER;}
        if(which==7) {f.hw->SetJointCommandEnabled(false);expected=R::SEND_GATE_CLOSED;}
        const auto sent=f.io->sends.load();
        bool threw=false;
        try {f.hw->SetJointCommand(cmd);} catch(const std::runtime_error&) {threw=true;}
        Check(threw==(which==6),"only simulated transport failure throws");
        Check(f.hw->LastStandRecord().reason==expected,"specific rejection classification");
        Check(!f.hw->JointCommandsEnabled() && f.io->sends==sent,"reject means no send");
        if(which==0) Check(f.hw->LastStandRecord().joint==4,"tracking joint index");
        f.sm->ReleaseHardwareControl();
        f.hw->SetJointCommand(cmd);
        Check(f.hw->LastStandRecord().reason==R::SEND_GATE_CLOSED,"closed gate classified");
        Check(f.io->sends==sent,"no post-release sends");
    }
}
void Mapping() {
    RobotData d{}; RobotCmd c{};
    for(int i=0;i<12;++i) {d.joint_data.joint_data[i].position=i+.25; c.joint_cmd[i].position=i+.5;}
    JointData* legs[]={d.joint_data.fl_leg,d.joint_data.fr_leg,d.joint_data.hl_leg,d.joint_data.hr_leg};
    JointCmd* cmds[]={c.fl_leg,c.fr_leg,c.hl_leg,c.hr_leg};
    for(int l=0;l<4;++l) for(int j=0;j<3;++j) {
        Check(legs[l][j].position==3*l+j+.25,"SDK feedback named/array mapping");
        Check(cmds[l][j].position==3*l+j+.5,"SDK command named/array mapping");
    }
}
void ExpiryAndTimestamp() {
    // Reproduces loss in the OLD absolute-float clock, without changing policy/trajectory.
    Check(float(2000000.001)==float(2000000.002),"old float timestamp collapses millisecond ticks");
    Replay f; f.Enter(); f.stand->Run(); auto cmd=f.hw->GetJointCommand();
    const auto sent=f.io->sends.load();
    std::this_thread::sleep_for(std::chrono::milliseconds(8050));
    f.Emit(); // fresh mock feedback, ONLY real permit deadline expires
    f.hw->SetJointCommand(cmd);
    Check(f.hw->LastStandRecord().reason==stand_diagnostics::Reason::PERMIT_EXPIRED,"active permit expiry classified");
    Check(f.io->sends==sent && !f.hw->JointCommandsEnabled(),"expired permit rejects before send");
    f.sm->ReleaseHardwareControl();
}
void InvalidRestingPose() {
    for(int joint:{4,10}) {
        Replay f;
        f.measured.joint_data.joint_data[joint].position=joint==4?2.50592f:1.46145f; f.Emit();
        Check(f.sm->AcquireHardwareControl(),"inert acquire only");
        Check(!f.sm->AuthorizeStandTest(true,true,true,true),"out-of-range resting pose rejects before authorization");
        Check(f.sm->StandPreflightReason().find("joint "+std::to_string(joint))!=std::string::npos,"specific preflight joint");
        Check(!f.sm->RequestStand() && f.io->sends==0 && !f.hw->JointCommandsEnabled(),"bad resting pose never streams");
    }
}
void InvalidIdleLoggingBounded() {
    Replay f; f.measured.joint_data.joint_data[4].position=2.506;f.Emit();f.idle->Run();
    std::ostringstream output; auto* previous=std::cout.rdbuf(output.rdbuf());
    bool stayed_idle=true;
    for(int i=0;i<1000;++i) stayed_idle &= f.idle->GetNextStateName()==kIdle;
    std::cout.rdbuf(previous);
    const auto s=output.str(); const auto first=s.find("joint status:");
    Check(stayed_idle && first!=std::string::npos && s.find("joint status:",first+1)==std::string::npos,
          "invalid posture still blocked without per-cycle console flood");
}
int main() {
    try {
        Mapping();
        FullReplay(1000,0); FullReplay(2000000000u,4.8); FullReplay(1000,0,true);
        FullReplay(1000,0,false,{.2,-.8,2.,-.2,-1.0,2.1,.1,-.9,2.2,-.1,-1.2,2.3});
        FullReplay(1000,0,false,{.1,-2.,1.5,-.1,-1.9,1.6,.15,-1.8,1.7,-.15,-1.7,1.8});
        GuardReasons(); ExpiryAndTimestamp(); InvalidRestingPose(); InvalidIdleLoggingBounded();
        std::cout<<"STAND RECOVERY: PASS; inert transports only, real network calls=0\n";
    } catch(const std::exception& e) {std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}
}
