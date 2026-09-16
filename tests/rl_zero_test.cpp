// One focused offline suite: real lifecycle + inert transport, no SDK/socket implementation.
#define main unused_control_safety_suite_main
#include "control_safety_test.cpp"
#undef main
#include <fstream>
#include <sstream>

static const std::string token="SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED";
struct ZeroPolicy : PolicyRunnerBase {
    std::atomic<int> calls{0};
    std::atomic<bool> nonzero{false}, invalid{false}, fail{false};
    ZeroPolicy():PolicyRunnerBase("inert-zero") {decimation_=1;}
    void OnEnter() override {}
    void DisplayPolicyInfo() override {}
    RobotAction GetRobotAction(const RobotBasicState& s) override {
        ++calls;
        if(!s.cmd_vel_normlized.isZero(0)) nonzero=true;
        if(fail) throw std::runtime_error("inert policy failure");
        RobotAction a;
        a.goal_joint_pos=s.joint_pos;
        a.goal_joint_vel=VecXf::Zero(12);a.tau_ff=VecXf::Zero(12);
        a.kp=VecXf::Constant(12,30);a.kd=VecXf::Constant(12,1);
        if(invalid) a.goal_joint_pos[0]=std::numeric_limits<float>::quiet_NaN();
        return a;
    }
};
struct Fixture : StandFixture {
    std::shared_ptr<ZeroPolicy> policy=std::make_shared<ZeroPolicy>();
    std::shared_ptr<RLControlStateONNX> worker;
    Fixture() {
        machine.reset();
        // Real clock for threaded hardware freshness: never read the fixture's
        // non-atomic synthetic monitor clock from the policy thread.
        hw=std::make_shared<HardwareInterface>("inert-rl",io,300ms);
        data->ri_ptr=hw;
        idle=std::make_shared<ModeState>(data,kIdle);
        stand=std::make_shared<StandUpState>(Lite3,"actual_vendor_stand",data);
        damping=std::make_shared<ModeState>(data,kJointDamping);
        worker=std::make_shared<RLControlStateONNX>(Lite3,"real_worker_inert_policy",data,policy);
        machine=std::make_unique<StateMachine>(hw,input,idle,stand,worker,damping,[this]{return wall;});
        Feedback();
    }
    void Reach() {
        Check(!machine->RequestRLZeroOnce(token),"no stand blocks RL-zero");
        Check(io->sends==0 && io->acquires==0,"passive startup");
        Enter();
        Check(!machine->RequestRLZeroOnce(token),"incomplete stand blocks RL-zero");
        for(int i=0;i<600 && machine->StandTestStatus()!="TARGET_REACHED";++i)Tick();
        Check(machine->StandTestStatus()=="TARGET_REACHED","stable stand");
    }
    void Begin() {
        Reach();
        Check(!machine->RequestRLZeroOnce("wrong") && !machine->RequestRLControl(),"explicit zero-only token required");
        const int sends=io->sends;
        Check(machine->RequestRLZeroOnce(token),"RL-zero transition");
        Check(io->sends==sends && policy->calls==0,"no inference or joint send before fresh Run");
        Check(!machine->IsHardwareControlAcquired(),"ownership remains unconfirmed");
        Check(!machine->RequestRLZeroOnce(token),"no reentry/extension");
        for(int i=0;i<30 && policy->calls==0;++i) {Tick();std::this_thread::sleep_for(1ms);}
        Check(policy->calls>0 && hw->JointCommandsEnabled(),"actual policy worker sends via guarded mock transport");
    }
    void Closed() {
        Check(!hw->JointCommandsEnabled() && io->releases==1,"closed gate and one return");
        const auto sends=io->sends.load(), calls=policy->calls.load();
        for(int i=0;i<3;++i) {Tick();std::this_thread::sleep_for(1ms);}
        Check(io->sends==sends && policy->calls==calls,"worker joined; no further inference or sends");
        Check(hw->IsFeedbackFresh(),"passive feedback continues");
        Check(!policy->nonzero,"policy always received exact zero");
        const auto v=input->GetUserCommand();
        Check(v.forward_vel_scale==0 && v.side_vel_scale==0 && v.turnning_vel_scale==0,"zero persists after exit");
    }
};
int main() {
    try {
        for(int fault=0;fault<9;++fault) {
            Fixture f;f.Begin();
            f.input->set_velocity_normalized(1,-1,.5);
            for(int i=0;i<5;++i) {f.Tick();std::this_thread::sleep_for(1ms);}
            Check(!f.policy->nonzero,"direct source updates cannot defeat zero lock");
            if(fault==0)f.machine->StopVelocity();
            if(fault==1)f.machine->ReleaseHardwareControl();
            if(fault==2){std::this_thread::sleep_for(310ms);f.machine->ProcessOnce();}
            if(fault==3){f.Feedback(true);f.machine->ProcessOnce();}
            if(fault==4){f.io->Emit(++f.tick*10,true);f.machine->ProcessOnce();}
            if(fault==5)f.machine->Shutdown();
            if(fault==6){f.wall+=8;f.Feedback();f.machine->ProcessOnce();
                Check(f.machine->StandAbortReason()=="RL zero 8s deadline","deadline distinguished");}
            if(fault==7 || fault==8) {
                if(fault==7)f.policy->invalid=true;else f.policy->fail=true;
                for(int i=0;i<50 && !f.io->releases;++i){f.Tick();std::this_thread::sleep_for(1ms);}
            }
            f.Closed();
        }
        {Fixture f;f.Reach();std::this_thread::sleep_for(310ms);Check(!f.machine->RequestRLZeroOnce(token),"stale entry blocked");}
        {Fixture f;f.Begin();std::this_thread::sleep_for(320ms);f.Feedback();f.machine->ProcessOnce();
            Check(f.machine->StandAbortReason()=="RL zero policy-send timeout 300ms","send silence distinguished");f.Closed();}
        {
            Fixture f;f.Begin();
            // Fill diagnostic ring without changing control; retain the newest abort evidence.
            for(int i=0;i<24010;++i) f.hw->RecordStandEvent(3,"inert overflow filler");
            f.hw->RecordStandEvent(3,"RL_DIAGNOSTIC_OVERFLOW_MARKER");
            const auto r=f.hw->LastStandRecord();
            Check(r.rl_zero && r.policy_completed>0 && r.policy_started>=r.policy_completed,
                  "policy progress captured after overflowing old stand records");
            Check(r.normalized[0]==0 && r.normalized[1]==0 && r.normalized[2]==0,"record actual policy input");
            std::ostringstream captured;
            auto* previous=std::cerr.rdbuf(captured.rdbuf());
            f.machine->StopVelocity();
            std::cerr.rdbuf(previous);
            const auto text=captured.str();const auto begin=text.find("STAND_TRACE ");
            Check(begin!=std::string::npos,"deferred log path");
            const auto path_start=begin+12;
            std::ifstream log(text.substr(path_start,text.find(' ',path_start)-path_start));
            std::string line;bool marker=false,abort=false;
            while(std::getline(log,line)) {
                if(line.find("RL_DIAGNOSTIC_OVERFLOW_MARKER")!=std::string::npos)marker=true;
                if(line.find("\"event_detail\":\"stop requested\"")!=std::string::npos) {
                    abort=line.find("\"phase\":\"RL_ZERO\"")!=std::string::npos;
                }
            }
            Check(marker && abort,"serialized ring keeps newest RL/abort records despite full buffer");
            f.Closed();
        }
        // Actual unchanged ONNX policy: first zero-input output at the final stand pose.
        // This checks software continuity only, NOT physical stability.
        {
            Fixture f;f.Reach();
            Lite3TestPolicyRunnerONNX policy("offline-zero-entry");policy.OnEnter();
            RobotBasicState s{};s.joint_pos=f.hw->GetJointPosition();s.joint_vel=VecXf::Zero(12);
            s.joint_tau=VecXf::Zero(12);s.base_rpy=Vec3f::Zero();s.base_rot_mat=Mat3f::Identity();
            s.projected_gravity=Vec3f(0,0,-1);s.base_omega=Vec3f::Zero();s.base_acc=Vec3f(0,0,9.81);
            s.cmd_vel_normlized=Vec3f::Zero();
            const auto action=policy.GetRobotAction(s).ConvertToMat();
            const float error=(action.col(1)-s.joint_pos).cwiseAbs().maxCoeff();
            Check(action.rows()==12 && action.allFinite(),"real ONNX zero action finite");
            std::cout<<"REAL_ONNX_ZERO_INITIAL_MAX_ERROR="<<error<<" rad\n";
            Check(error<=.35,"real ONNX entry fits unchanged tracking guard");
            f.machine->ReleaseHardwareControl();
        }
        std::cout<<"PASS: RL-zero transition, one-way zero lock, guarded sends, failures, stop/join/release, timeout; inert transport only\n";
    } catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}
}
