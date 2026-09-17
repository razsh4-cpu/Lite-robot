// Supported-success lifecycle tests. Injected inert SDK; no robot sockets.
#define main unused_control_safety_suite_main
#include "control_safety_test.cpp"
#undef main

static void Reach(StandFixture& f) {
    f.Enter();
    for(int i=0;i<600 && f.machine->StandTestStatus()!="TARGET_REACHED";++i) f.Tick();
    Check(f.machine->StandTestStatus()=="TARGET_REACHED","measured convergence required");
    Check(f.io->releases==0 && f.hw->JointCommandsEnabled(),"success retains gate/request");
    Check(!f.machine->IsHardwareControlAcquired(),"ownership still unconfirmed");
}
static void Closed(StandFixture& f,int sends) {
    Check(!f.hw->JointCommandsEnabled() && f.io->releases==1,"abort closes and releases once");
    Check(f.io->sends==sends,"no send after fault/operator action");
    const auto v=f.machine->VelocitySnapshot();
    Check(v.forward_vel_scale==0 && v.side_vel_scale==0 && v.turnning_vel_scale==0,"zero input");
    f.machine->ReleaseHardwareControl(); f.machine->ProcessOnce();
    Check(f.io->releases==1 && f.io->sends==sends,"idempotent release/no further sends");
}
static void Hold() {
    StandFixture f; Reach(f);
    const auto reached=f.wall;
    while(f.io->releases==0 && f.wall-reached<2.1) {
        f.Tick();
        if(f.io->releases==0) {
            Check(f.machine->StandTestStatus()=="TARGET_REACHED","successful target remains monitored");
            Check(f.hw->JointCommandsEnabled() && !f.machine->RequestRLControl(),"stand only, RL blocked");
            const auto cmd=f.hw->GetJointCommand();
            for(int j=0;j<12;++j) Check(std::abs(cmd(j,3))<.001,"final zero-velocity target held");
        }
    }
    Check(f.io->releases==1,"successful target automatically releases");
    Check(f.wall-reached>=2.0 && f.wall-reached<2.02,"target hold bounded to two seconds");
    Check(f.machine->StandAbortReason()=="stand target hold complete","automatic release reason");
    const auto sends=f.io->sends.load(); Closed(f,sends);
    std::cout<<"PASS: supported target hold automatically releases after two seconds\n";
}
static void Faults() {
    for(int failure=0;failure<9;++failure) {
        StandFixture f; Reach(f); const auto sends=f.io->sends.load();
        if(failure==0) f.machine->StopVelocity();
        if(failure==1) f.machine->ReleaseHardwareControl();
        if(failure==2) {f.wall+=.301; f.machine->ProcessOnce();}
        if(failure==3) {f.io->Emit(++f.tick*10,true);f.machine->ProcessOnce();}
        if(failure==4) {f.Feedback(true);f.machine->ProcessOnce();}
        if(failure==5 || failure==6) {
            RobotData d{};d.tick=++f.tick*10;d.imu.acc_z=9.81;
            const auto cmd=f.hw->GetJointCommand();
            for(int j=0;j<12;++j)d.joint_data.joint_data[j].position=cmd(j,1);
            d.joint_data.joint_data[0].position+=failure==5?.36f:.09f;
            f.io->callback(d);f.machine->ProcessOnce();
        }
        if(failure==7) {
            auto cmd=f.hw->GetJointCommand();cmd(0,1)=std::numeric_limits<float>::quiet_NaN();
            f.hw->SetJointCommand(cmd);f.machine->ProcessOnce();
        }
        if(failure==8) f.machine->Shutdown();
        Closed(f,sends);
        std::cout<<"FAULT "<<failure<<": "<<f.machine->StandAbortReason()<<'\n';
    }
    {
        StandFixture f;Reach(f);const auto sends=f.io->sends.load();
        // Pause the worker, not the private real-time lease. The fixture's
        // injected monitor clock isolates lease expiry from telemetry guards.
        std::this_thread::sleep_for(8050ms);
        f.Tick();
        Check(f.machine->StandAbortReason()=="stand hold permit expired or cancelled",
              "expired hold lease cannot be revived by otherwise-valid feedback");
        Closed(f,sends);
    }
    std::cout<<"PASS: failure/stop/release/shutdown unchanged; stopped worker cannot renew expired lease\n";
}
static void ReleaseOnly() {
    StandFixture f;Reach(f);
    const auto sends=f.io->sends.load();
    const auto stamp=f.hw->GetStandFeedback().stamp;
    // Exact validation-console `release` branch, not just its second call.
    f.machine->StopVelocity();
    f.machine->ReleaseHardwareControl();
    Check(f.machine->StandAbortReason()=="stop requested","console release reason is truthful");
    Check(f.machine->StandTestStatus()=="RELEASE_REQUESTED","release status");
    Check(!f.machine->IsControlRequestSent(),"request cleared, not an ownership acknowledgement");
    Check(std::string(f.machine->OwnershipStatus())=="NOT_REQUESTED","honest local ownership label");
    Closed(f,sends);
    for(int i=0;i<10;++i) {
        f.Tick();
        Check(f.machine->TelemetryFresh(),"fresh passive feedback after release");
        Check(!f.hw->JointCommandsEnabled() && f.io->sends==sends,"no later joint transmission");
    }
    Check(f.hw->GetStandFeedback().stamp>stamp,"passive feedback progresses after release");
    Check(f.io->releases==1,"one ownership return only");
    // Worker ticks after release must not leave SoftwareVelocityInterface
    // stopped. A new acquisition epoch must accept exactly one new stand.
    Check(f.machine->AcquireHardwareControl(),"reacquire after completed release");
    Check(f.machine->RequestStandOnce("SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED"),
          "post-release stand request accepted without restarting process");
    Check(!f.hw->JointCommandsEnabled(),"new request remains pending with gate closed");
    f.machine->StopVelocity();
    std::cout<<"PASS: exact console release; gate closed, no further joints, one return request, passive telemetry progresses\n";
}
int main(int argc,char** argv) {
    try {
        Check(argc==2,"select --hold, --faults or --release");
        if(std::string(argv[1])=="--hold")Hold();
        else if(std::string(argv[1])=="--release")ReleaseOnly();
        else {Check(std::string(argv[1])=="--faults","known mode");Faults();}
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
