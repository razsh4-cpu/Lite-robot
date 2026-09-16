// Focused inert test: production state machine + injected mock SDK only.
// Reuse fixtures, but do not run the general safety suite.
#define main unused_control_safety_suite_main
#include "control_safety_test.cpp"
#undef main

static constexpr const char* confirmation="SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED";
static void Zero(StateMachine& machine) {
    const auto v=machine.VelocitySnapshot();
    Check(v.forward_vel_scale==0 && v.side_vel_scale==0 && v.turnning_vel_scale==0,
          "all normalized velocity remains zero");
}

int main() {
    try {
        for(int failure=0;failure<7;++failure) {
            StandFixture f;
            if(failure!=0) Check(f.machine->AcquireHardwareControl(),"inert acquire");
            std::string token=confirmation;
            if(failure==1) f.wall+=.301; // stale
            if(failure==2) f.io->Emit(++f.tick*10,true); // nonfinite IMU
            if(failure==3) f.Feedback(true); // tilt/preflight
            if(failure==4) token="";
            if(failure==5) token+=" extra";
            if(failure==6) {
                MotionStateFeedback feedback;
                feedback.UpdateCurrentState(RLControlMode);
                f.input->SetMotionStateFeedback(feedback);
                f.input->set_velocity_normalized(.05,0,0);
                Check(f.machine->VelocitySnapshot().forward_vel_scale!=0,"inject nonzero input");
            }
            Check(!f.machine->RequestStandOnce(token),"failed prerequisite rejects combined action");
            Check(f.machine->StandTestStatus()=="LOCKED","no authorization on failed prerequisites");
            Check(!f.hw->JointCommandsEnabled() && f.io->sends==0,"rejection cannot send joints");
            Check(!f.machine->RequestRLControl(),"no RL path");
        }
        {
            StandFixture f(false);
            Check(!f.machine->RequestStandOnce(confirmation),"never-received feedback rejected");
            Check(f.io->acquires==0 && f.io->sends==0,"no automatic ownership or send");
        }
        {
            StandFixture f;
            Check(f.machine->AcquireHardwareControl(),"inert acquire");
            Check(f.machine->RequestStandOnce(confirmation),"combined action accepted");
            Check(f.machine->StandTestStatus()=="PENDING","exactly one request pending");
            Check(!f.machine->RequestStandOnce(confirmation) && !f.machine->RequestStand(),"cannot queue second request");
            Check(!f.hw->JointCommandsEnabled() && f.io->sends==0,"pending gate stays closed");
            Check(!f.machine->IsHardwareControlAcquired(),"ownership remains unconfirmed");
            Check(f.input->GetUserCommand().target_mode==StandingUp,"only stand requested");
            Zero(*f.machine);
            f.Tick();
            Check(f.machine->StandTestStatus()=="STANDING_UP","existing guarded transition");
            Check(f.hw->JointCommandsEnabled() && f.io->sends==0,"entry precedes first send");
            Check(!f.machine->RequestStandOnce(confirmation),"open gate/active stand rejects combined action");
            Check(!f.machine->RequestRLControl(),"RL remains blocked");
            f.machine->SetVelocityNormalized(.05,.05,.05);
            Zero(*f.machine);
            Check(f.io->sends==0 && !f.hw->JointCommandsEnabled(),"velocity misuse aborts without sending");
        }
        {
            StandFixture f; f.Arm();
            f.wall=5.01; f.Feedback();
            Check(!f.machine->RequestStand(),"unused expired authorization rejected");
            f.machine->ProcessOnce();
            Check(f.machine->StandAbortReason()=="stand authorization expired","existing expiry fails closed");
            Check(f.io->sends==0 && f.io->releases==1,"expiry releases without joints");
            Check(!f.machine->RequestStandOnce(confirmation),"combined action cannot reset expired latch");
        }
        {
            StandFixture f; f.Arm();
            f.wall=4.9; f.Feedback();
            Check(f.machine->RequestStand(),"request accepted before expiry");
            f.Tick();
            for(int i=0;i<20;++i) f.Tick();
            Check(f.wall>5 && f.machine->StandTestStatus()=="STANDING_UP",
                  "consumed arm deadline does not abort active stand");
            Check(f.io->releases==0,"active stand keeps existing independent guards");
            Zero(*f.machine);
        }
        std::cout<<"stand_once focused inert tests: PASS\n";
        return 0;
    } catch(const std::exception& error) {
        std::cerr<<"stand_once test: "<<error.what()<<'\n'; return 1;
    }
}
