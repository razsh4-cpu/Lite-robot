// Actual monitor/state/trajectory; inert transport only. No robot sockets.
#define main unused_control_safety_suite_main
#include "control_safety_test.cpp"
#undef main
#include <fstream>
#include <sstream>

static double Number(const std::string& line,const std::string& key) {
    const auto p=line.find("\""+key+"\":");
    Check(p!=std::string::npos,"trace scalar exists");
    return std::stod(line.substr(p+key.size()+3));
}
static std::array<double,12> Array(const std::string& line,const std::string& key) {
    const auto p=line.find("\""+key+"\":[");
    Check(p!=std::string::npos,"trace array exists");
    auto values=line.substr(p+key.size()+4);
    values=values.substr(0,values.find(']')); std::replace(values.begin(),values.end(),',',' ');
    std::istringstream input(values); std::array<double,12> result{};
    for(auto& x:result) Check(bool(input>>x),"12 finite trace values");
    return result;
}
static void Recorded(const char* path) {
    std::ifstream input(path); Check(bool(input),"recorded hardware trace available");
    supervised_stand::Monitor monitor; monitor.Start(0);
    supervised_stand::Sample sample;
    std::array<double,12> previous_target{},previous_dq{};
    bool have=false; double previous_elapsed=0,start=0,largest=0,final_error=0,longest=0;
    double reached=-1,strict_start=-1;
    int rows=0,speed_failures=0,largest_joint=-1;
    for(std::string line;std::getline(input,line);) {
        if(line.find("\"event\":1,")!=std::string::npos) start=Number(line,"wall_s");
        if(line.find("\"sent\":1,")==std::string::npos) continue;
        ++rows;
        const double t=Number(line,"wall_s")-start, elapsed=Number(line,"elapsed_s");
        sample.position=Array(line,"position"); sample.velocity=Array(line,"velocity");
        sample.target=previous_target; sample.target_velocity=previous_dq;
        sample.fresh=true; sample.target_valid=have; sample.final_target=have && previous_elapsed>=3;
        sample.roll=Number(line,"roll"); sample.pitch=Number(line,"pitch");
        const auto result=monitor.Check(t,sample);
        Check(result!=supervised_stand::Result::Abort,"recorded successful stand remains monitored without release");
        if(result==supervised_stand::Result::TargetReached && reached<0) reached=t;
        const double raw_speed=*std::max_element(sample.velocity.begin(),sample.velocity.end(),
            [](double a,double b){return std::abs(a)<std::abs(b);});
        bool strict=sample.target_valid && sample.final_target;
        for(int j=0;j<12;++j) strict &= std::abs(sample.position[j]-sample.target[j])<=.08 &&
            std::abs(sample.velocity[j])<=.15 && std::abs(sample.target_velocity[j])<=.001;
        if(strict) {if(strict_start<0)strict_start=t;longest=std::max(longest,t-strict_start);}
        else strict_start=-1;
        const auto err=Number(line,"max_error");
        if(err>largest) {largest=err;largest_joint=int(Number(line,"joint"));}
        if(elapsed>=3) {
            final_error=std::max(final_error,err);
            if(std::abs(raw_speed)>.15) ++speed_failures;
        }
        previous_target=Array(line,"target"); previous_dq=Array(line,"target_velocity");
        previous_elapsed=elapsed;have=true;
    }
    Check(rows==5928,"complete recorded sent interval");
    Check(reached>=3.5 && reached<4,"recorded response reaches corrected convergence before deadline");
    Check(monitor.diagnostics().observation_elapsed>2,"hold continues after two seconds");
    Check(final_error<.08 && largest<.35 && speed_failures>0 && longest<.5,"speed dwell is blocker");
    std::cout<<"RECORDED rows="<<rows<<" max_error="<<largest<<" joint="<<largest_joint
             <<" final_error="<<final_error<<" speed_failures="<<speed_failures
             <<" previous_strict_longest_dwell="<<longest<<" corrected_reached_s="<<reached
             <<" automatic_release=NO result="<<monitor.reason()<<'\n';
}

static void Synthetic(double lag, double bias) {
    // First-order measured response to actual accepted trajectory targets, not
    // a physical dynamics model. Includes representative knee load offsets.
    StandFixture f;
    const std::array<float,12> initial={-.446434,-1.160201,2.73911,.436433,-1.163203,2.74174,
                                      -.445512,-1.149393,2.745181,.440858,-1.147944,2.747343};
    RobotData d{};d.imu.acc_z=9.81;
    for(int j=0;j<12;++j)d.joint_data.joint_data[j].position=initial[j];
    auto emit=[&]{d.tick=++f.tick*10; f.io->callback(d);}; emit();
    Check(f.machine->AcquireHardwareControl() && f.machine->RequestStandOnce(
          "SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED"),"inert supervised request");
    f.wall+=.01;emit(); f.machine->ProcessOnce();
    Check(f.machine->StandTestStatus()=="STANDING_UP","entered before sends");
    const double start=f.wall; double reached=-1,max_error=0;
    for(int i=0;i<700 && f.io->releases==0;++i) {
        const auto target=f.hw->GetJointCommand();
        if(f.io->sends>0) for(int j=0;j<12;++j) {
            const double offset=(j%3==2?bias:0);
            const double old=d.joint_data.joint_data[j].position;
            const double next=old+(target(j,1)+offset-old)*(1-std::exp(-.01/lag));
            d.joint_data.joint_data[j].position=next;
            d.joint_data.joint_data[j].velocity=(next-old)/.01;
        }
        f.wall+=.01; emit(); f.machine->ProcessOnce();
        if(f.machine->StandTestStatus()=="TARGET_REACHED" && reached<0) reached=f.wall-start;
        const auto record=f.hw->LastStandRecord();
        if(record.sent) max_error=std::max(max_error,record.max_error);
        Check(!f.machine->RequestRLControl(),"RL blocked");
        Check(f.io->releases==0,"no successful-stand auto-release");
    }
    Check(reached>=0 && f.io->releases==0,"slower model converges and holds");
    f.machine->StopVelocity();
    Check(f.machine->StandAbortReason()=="stop requested" && f.io->releases==1,"explicit stop releases");
    Check(!f.hw->JointCommandsEnabled(),"release gate closed");
    const auto last=f.hw->LastStandRecord();
    Check(last.event==2 && last.event_detail=="stop requested","exact release cause logged");
    Check(last.monitor.observation_elapsed>=1.99 && last.monitor.dwell_elapsed>=.5,
          "monitor timing logged at release");
    std::cout<<"SYNTHETIC lag="<<lag<<" knee_bias="<<bias<<" reached_s="<<reached
             <<" release_s="<<f.wall-start<<" max_error="<<max_error<<'\n';
}
int main(int argc,char** argv) {
    try {
        Check(argc==2,"provide recorded trace path"); Recorded(argv[1]);
        Synthetic(.025,.04); Synthetic(.075,.05); Synthetic(.15,.05);
        std::cout<<"PASS: approved windowed convergence; recorded and slower responses converge; no network\n";
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
