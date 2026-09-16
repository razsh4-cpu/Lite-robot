#include <mujoco/mujoco.h>

#include "lite3_test_policy_runner_onnx.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

namespace {
constexpr double kDt = 0.001;
constexpr double kZeroSeconds = 2.0;
constexpr double kCommandSeconds = 5.0;

struct Result {
    double command=0, dx=0, mean_vx_tail=0, max_tilt=0, min_height=0;
    double dx_at_1s=0, max_target_span_1s=0;
    double first_1cm=-1, first_5cm=-1, sustained_vx=-1, four_contacts=-1;
    double max_tracking_error=0, max_knee_tracking_error=0;
    double max_joint_speed=0, max_applied_torque=0;
    int contact_transitions=0, contacts_at_1s=0;
    std::array<double,12> command_start_q{}, first_command_target{};
    std::array<double,45> first_command_observation{};
    std::array<double,12> first_command_raw_action{};
    std::array<double,45> last_first_second_observation{};
    std::array<double,12> last_first_second_raw_action{};
    bool stable=false, walking=false;
    bool targets_finite=true, targets_in_joint_limits=true;
};

Result Run(const std::string& model_path, double command, double actuator_scale) {
    char error[1024]{};
    std::unique_ptr<mjModel, decltype(&mj_deleteModel)> model(
        mj_loadXML(model_path.c_str(), nullptr, error, sizeof(error)), mj_deleteModel);
    if(!model) throw std::runtime_error(std::string("MuJoCo model load failed: ")+error);
    std::unique_ptr<mjData, decltype(&mj_deleteData)> data(mj_makeData(model.get()), mj_deleteData);
    model->opt.timestep=kDt;
    mj_resetData(model.get(),data.get());
    data->qpos[0]=0; data->qpos[1]=0; data->qpos[2]=0.36;
    data->qpos[3]=1; data->qpos[4]=data->qpos[5]=data->qpos[6]=0;
    for(int leg=0;leg<4;++leg){data->qpos[7+leg*3]=0;data->qpos[8+leg*3]=-.80;data->qpos[9+leg*3]=1.60;}
    mju_zero(data->qvel,model->nv); mj_forward(model.get(),data.get());

    Lite3TestPolicyRunnerONNX policy("mujoco-sweep-"+std::to_string(command));
    policy.OnEnter();
    RobotAction action;
    action.goal_joint_pos=VecXf::Zero(12);action.goal_joint_vel=VecXf::Zero(12);
    action.tau_ff=VecXf::Zero(12);action.kp=VecXf::Constant(12,30);action.kd=VecXf::Constant(12,1);
    for(int leg=0;leg<4;++leg){action.goal_joint_pos[leg*3]=0;action.goal_joint_pos[leg*3+1]=-.80;action.goal_joint_pos[leg*3+2]=1.60;}

    const int torso=mj_name2id(model.get(),mjOBJ_BODY,"TORSO");
    const int floor=mj_name2id(model.get(),mjOBJ_GEOM,"floor");
    const char* foot_names[4]={"FL_FOOT_collision","FR_FOOT_collision","HL_FOOT_collision","HR_FOOT_collision"};
    std::array<int,4> feet{};for(int i=0;i<4;++i)feet[i]=mj_name2id(model.get(),mjOBJ_GEOM,foot_names[i]);
    std::array<bool,4> previous_contact{};bool have_contact=false;
    Result result;result.command=command;result.min_height=1e9;
    double command_start_x=0,tail_vx_sum=0,fast_since=-1;int tail_samples=0;
    std::array<double,12> target_min{},target_max{};
    target_min.fill(1e9);target_max.fill(-1e9);
    bool command_boundary_captured=false;
    const int steps=static_cast<int>((kZeroSeconds+kCommandSeconds)/kDt);
    for(int step=0;step<steps;++step){
        const double t=step*kDt;
        if(step%policy.decimation_==0){
            RobotBasicState state{};
            state.joint_pos=VecXf(12);state.joint_vel=VecXf(12);state.joint_tau=VecXf(12);
            for(int i=0;i<12;++i){state.joint_pos[i]=data->qpos[7+i];state.joint_vel[i]=data->qvel[6+i];state.joint_tau[i]=data->qfrc_actuator[6+i];}
            state.base_rot_mat=Eigen::Map<const Eigen::Matrix<double,3,3,Eigen::RowMajor>>(data->xmat+9*torso).cast<float>();
            state.base_omega=Vec3f(data->qvel[3],data->qvel[4],data->qvel[5]);
            state.base_acc=Vec3f::Zero();state.base_rpy=Vec3f::Zero();state.projected_gravity=Vec3f(0,0,-1);
            state.cmd_vel_normlized=Vec3f(t>=kZeroSeconds?command:0,0,0);
            action=policy.GetRobotAction(state);
            for(int i=0;i<12;++i) {
                const double target=action.goal_joint_pos[i];
                result.targets_finite=result.targets_finite&&std::isfinite(target);
                const int joint=i%3;
                const double lower=joint==0?-.530:joint==1?-3.50:.349;
                const double upper=joint==0?.530:joint==1?.320:2.80;
                result.targets_in_joint_limits=result.targets_in_joint_limits&&target>=lower&&target<=upper;
            }
            if(t>=kZeroSeconds && !command_boundary_captured) {
                for(int i=0;i<12;++i) {
                    result.command_start_q[i]=data->qpos[7+i];
                    result.first_command_target[i]=action.goal_joint_pos[i];
                }
                if(!policy.GetDiagnosticSnapshot(result.first_command_observation,
                                                 result.first_command_raw_action))
                    throw std::runtime_error("policy diagnostic snapshot unavailable");
                command_boundary_captured=true;
            }
            if(t>=kZeroSeconds && t<kZeroSeconds+1.0)for(int i=0;i<12;++i){
                target_min[i]=std::min(target_min[i],double(action.goal_joint_pos[i]));
                target_max[i]=std::max(target_max[i],double(action.goal_joint_pos[i]));
            }
            if(t>=kZeroSeconds && t<kZeroSeconds+1.0)
                policy.GetDiagnosticSnapshot(result.last_first_second_observation,
                                             result.last_first_second_raw_action);
        }
        for(int i=0;i<12;++i){
            const double tau=action.kp[i]*(action.goal_joint_pos[i]-data->qpos[7+i])+
                action.kd[i]*(action.goal_joint_vel[i]-data->qvel[6+i])+action.tau_ff[i];
            data->ctrl[i]=actuator_scale*std::clamp(tau,-30.0,30.0);
            if(t>=kZeroSeconds) {
                const double error=std::abs(action.goal_joint_pos[i]-data->qpos[7+i]);
                result.max_tracking_error=std::max(result.max_tracking_error,error);
                if(i%3==2) result.max_knee_tracking_error=std::max(result.max_knee_tracking_error,error);
                result.max_joint_speed=std::max(result.max_joint_speed,std::abs(data->qvel[6+i]));
                result.max_applied_torque=std::max(result.max_applied_torque,std::abs(data->ctrl[i]));
            }
        }
        mj_step(model.get(),data.get());
        if(step==static_cast<int>(kZeroSeconds/kDt)) command_start_x=data->qpos[0];
        if(t>=kZeroSeconds){
            const double command_elapsed=t-kZeroSeconds;
            const double displacement=std::abs(data->qpos[0]-command_start_x);
            if(result.first_1cm<0&&displacement>=.01)result.first_1cm=command_elapsed;
            if(result.first_5cm<0&&displacement>=.05)result.first_5cm=command_elapsed;
            if(std::abs(data->qvel[0])>=.03){
                if(fast_since<0)fast_since=command_elapsed;
                if(result.sustained_vx<0&&command_elapsed-fast_since>=.20)result.sustained_vx=fast_since;
            }else fast_since=-1;
            result.min_height=std::min(result.min_height,data->qpos[2]);
            double mat[9];mju_quat2Mat(mat,data->qpos+3);
            const double roll=std::atan2(mat[7],mat[8]);
            const double pitch=std::asin(std::clamp(-mat[6],-1.0,1.0));
            result.max_tilt=std::max(result.max_tilt,std::max(std::abs(roll),std::abs(pitch)));
            if(t>=kZeroSeconds+kCommandSeconds-2){tail_vx_sum+=data->qvel[0];++tail_samples;}
            if(step%10==0){
                std::array<bool,4> contact{};
                for(int c=0;c<data->ncon;++c)for(int f=0;f<4;++f)
                    if((data->contact[c].geom1==floor&&data->contact[c].geom2==feet[f])||
                       (data->contact[c].geom2==floor&&data->contact[c].geom1==feet[f]))contact[f]=true;
                if(have_contact)for(int f=0;f<4;++f)if(contact[f]!=previous_contact[f])++result.contact_transitions;
                if(result.four_contacts<0&&result.contact_transitions>=4)result.four_contacts=command_elapsed;
                previous_contact=contact;have_contact=true;
            }
        }
        if(step==static_cast<int>((kZeroSeconds+1.0)/kDt)){
            result.dx_at_1s=data->qpos[0]-command_start_x;
            result.contacts_at_1s=result.contact_transitions;
        }
    }
    for(int i=0;i<12;++i)result.max_target_span_1s=std::max(result.max_target_span_1s,target_max[i]-target_min[i]);
    result.dx=data->qpos[0]-command_start_x;
    result.mean_vx_tail=tail_samples?tail_vx_sum/tail_samples:0;
    result.stable=result.min_height>.20&&result.max_tilt<.50;
    result.walking=result.stable&&std::abs(result.dx)>.05&&std::abs(result.mean_vx_tail)>.015&&result.contact_transitions>=4;
    return result;
}
}

int main(int argc,char**argv){
    try{
        if(argc<2||argc>4)throw std::runtime_error("usage: policy_mujoco_sweep MODEL.xml [normalized_forward [actuator_scale]]");
        std::cout<<"normalized,policy_forward,dx_m,dx_at_1s_m,tail_vx_mps,contact_transitions,contacts_at_1s,max_target_span_1s,first_1cm_s,first_5cm_s,sustained_vx_s,four_contact_changes_s,min_height_m,max_tilt_rad,max_tracking_error,max_knee_tracking_error,max_joint_speed,max_applied_torque,targets_finite,targets_in_joint_limits,classification\n";
        const int first=0,last=argc>=3?0:10;
        for(int i=first;i<=last;++i){
            const double command=argc>=3?std::stod(argv[2]):.05*i;
            const double actuator_scale=argc==4?std::stod(argv[3]):1.0;
            const auto r=Run(argv[1],command,actuator_scale);
            std::cout<<std::fixed<<std::setprecision(6)<<r.command<<','<<.8*r.command<<','<<r.dx<<','<<r.dx_at_1s<<','
                <<r.mean_vx_tail<<','<<r.contact_transitions<<','<<r.contacts_at_1s<<','<<r.max_target_span_1s<<','<<r.first_1cm<<','<<r.first_5cm<<','
                <<r.sustained_vx<<','<<r.four_contacts<<','<<r.min_height<<','<<r.max_tilt<<','
                <<r.max_tracking_error<<','<<r.max_knee_tracking_error<<','<<r.max_joint_speed<<','<<r.max_applied_torque<<','
                <<r.targets_finite<<','<<r.targets_in_joint_limits<<','
                <<(r.walking?"WALKING":r.stable?"POSTURE_ONLY":"UNSTABLE")<<'\n';
            if(argc==3) {
                std::cout<<"command_start_q";for(double v:r.command_start_q)std::cout<<','<<v;std::cout<<'\n';
                std::cout<<"first_command_target";for(double v:r.first_command_target)std::cout<<','<<v;std::cout<<'\n';
                std::cout<<"first_command_observation";for(double v:r.first_command_observation)std::cout<<','<<v;std::cout<<'\n';
                std::cout<<"first_command_raw_action";for(double v:r.first_command_raw_action)std::cout<<','<<v;std::cout<<'\n';
                std::cout<<"last_first_second_observation";for(double v:r.last_first_second_observation)std::cout<<','<<v;std::cout<<'\n';
                std::cout<<"last_first_second_raw_action";for(double v:r.last_first_second_raw_action)std::cout<<','<<v;std::cout<<'\n';
            }
            if(!r.targets_finite||!r.targets_in_joint_limits)return 1;
        }
    }catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}
}
