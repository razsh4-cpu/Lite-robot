#define main unused_control_safety_suite_main
#include "control_safety_test.cpp"
#undef main
#include <mutex>

struct CapturePolicy : PolicyRunnerBase {
    std::mutex mutex;std::vector<Vec3f> commands;
    CapturePolicy():PolicyRunnerBase("inert-forward-capture"){decimation_=1;}
    void DisplayPolicyInfo()override{} void OnEnter()override{}
    RobotAction GetRobotAction(const RobotBasicState& s)override{
        {std::lock_guard<std::mutex> l(mutex);commands.push_back(s.cmd_vel_normlized);}
        RobotAction a;a.goal_joint_pos=s.joint_pos;a.goal_joint_vel=VecXf::Zero(12);
        a.tau_ff=VecXf::Zero(12);a.kp=VecXf::Constant(12,30);a.kd=VecXf::Constant(12,1);return a;
    }
};
struct ForwardFixture:StandFixture{
    std::shared_ptr<CapturePolicy> policy=std::make_shared<CapturePolicy>();
    std::shared_ptr<RLControlStateONNX> worker;
    ForwardFixture(){
        machine.reset();hw=std::make_shared<HardwareInterface>("inert-forward",io,300ms);data->ri_ptr=hw;
        idle=std::make_shared<ModeState>(data,kIdle);stand=std::make_shared<StandUpState>(Lite3,"stand",data);
        damping=std::make_shared<ModeState>(data,kJointDamping);
        worker=std::make_shared<RLControlStateONNX>(Lite3,"rl-forward",data,policy);
        machine=std::make_unique<StateMachine>(hw,input,idle,stand,worker,damping,[this]{return wall;});Feedback();
    }
    void Reach(){Enter();for(int i=0;i<600&&machine->StandTestStatus()!="TARGET_REACHED";++i)Tick();
        Check(machine->StandTestStatus()=="TARGET_REACHED","converged stand required");}
};
int main(){try{
    const std::string token="SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED";
    ForwardFixture f;
    Check(!f.machine->RequestForwardOnce(token),"cannot enter before supported stand");
    f.Reach();Check(!f.machine->RequestForwardOnce("wrong"),"exact token required");
    const int before=f.io->sends;
    const double test_start=f.wall;
    Check(f.machine->RequestForwardOnce(token),"one-shot accepted");
    Check(!f.machine->RequestForwardOnce(token),"cannot repeat");
    Check(f.io->sends==before,"entry sends no joint packet before fresh RL update");
    double began=-1,ended=-1;
    for(int i=0;i<230;++i){
        f.Tick();const auto c=f.machine->VelocitySnapshot();
        Check(c.side_vel_scale==0&&c.turnning_vel_scale==0,"lateral/yaw fixed zero");
        Check(c.forward_vel_scale==0||c.forward_vel_scale==.25f,"only fixed forward value");
        if(c.forward_vel_scale>.0f&&began<0)began=f.wall;
        if(began>=0&&c.forward_vel_scale==0&&ended<0)ended=f.wall;
        std::this_thread::sleep_for(1ms);
    }
    Check(began-test_start>=1.0&&began-test_start<=1.02&&
          ended-began>=.99&&ended-began<=1.01,"1s zero then bounded 1000ms pulse");
    {std::lock_guard<std::mutex> l(f.policy->mutex);bool pulse=false,postzero=false;
      for(const auto& c:f.policy->commands){Check(c[1]==0&&c[2]==0,"policy never receives lateral/yaw");
        Check(c[0]==0||c[0]==.25f,"policy receives only zero/fixed pulse");if(c[0]==.25f)pulse=true;else if(pulse)postzero=true;}
      Check(pulse&&postzero,"policy observed pulse and automatic zero");}
    f.machine->StopVelocity();Check(f.io->releases==1&&!f.hw->JointCommandsEnabled(),"stop closes and releases");
    const int sends=f.io->sends;for(int i=0;i<3;++i)f.Tick();Check(f.io->sends==sends,"no send after stop");
    // Unchanged real ONNX policy must produce a finite first +0.05 action that
    // remains inside the existing 0.35-rad command/measurement tracking guard.
    Lite3TestPolicyRunnerONNX real("offline-forward-entry");real.OnEnter();RobotBasicState s{};
    s.joint_pos=f.hw->GetJointPosition();s.joint_vel=VecXf::Zero(12);s.joint_tau=VecXf::Zero(12);
    s.base_rot_mat=Mat3f::Identity();s.projected_gravity=Vec3f(0,0,-1);s.base_acc=Vec3f(0,0,9.81);
    s.base_rpy=s.base_omega=Vec3f::Zero();s.cmd_vel_normlized=Vec3f(.25,0,0);
    const auto a=real.GetRobotAction(s).ConvertToMat();const float e=(a.col(1)-s.joint_pos).cwiseAbs().maxCoeff();
    Check(a.allFinite()&&e<=.35,"real ONNX forward action finite/within unchanged guard");
    std::array<double,45> observation{};std::array<double,12> raw_action{};
    Check(real.GetDiagnosticSnapshot(observation,raw_action),"policy diagnostic snapshot available");
    Check(std::abs(observation[6]-.20)<1e-6 && observation[7]==0 && observation[8]==0,
          "snapshot contains scaled +0.25/zero/zero command");
    for(double value:raw_action)Check(std::isfinite(value),"snapshot raw action finite");
    std::cout<<"REAL_ONNX_FORWARD_INITIAL_MAX_ERROR="<<e<<" rad\n";
    std::cout<<"PASS: 1s zero, +0.25/1.00s one-shot, automatic zero, guarded stop/release; inert transport\n";
 }catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
