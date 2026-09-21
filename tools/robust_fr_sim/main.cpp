// Offline-only: links MuJoCo and Eigen, never the robot SDK or controller.
#include <Eigen/Dense>
#include "tools/lite3_leg_kinematics.hpp"
#include <mujoco/mujoco.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

using V2 = Eigen::Vector2d;
using V3 = Eigen::Vector3d;
using Q = Eigen::Matrix<double,12,1>;
constexpr double DT=.001, DELTA=.03, SPEED=.10, MEASURED=.50, TRACK=.15;
constexpr double ANGLE=3.0*3.141592653589793/180, CONTACT=2., MARGIN=.001;
const V3 STAND(0.,-.7729795255029084,1.5005003509817765);
double cross(V2 a,V2 b){return a.x()*b.y()-a.y()*b.x();}
std::vector<V2> hull(std::vector<V2> p){
  std::sort(p.begin(),p.end(),[](auto a,auto b){return a.x()==b.x()?a.y()<b.y():a.x()<b.x();});
  if(p.size()<3)return {};
  std::vector<V2> h;
  for(auto a:p){while(h.size()>1&&cross(h.back()-h[h.size()-2],a-h.back())<=0)h.pop_back();h.push_back(a);}
  size_t lower=h.size();
  for(int i=int(p.size())-2;i>=0;--i){while(h.size()>lower&&cross(h.back()-h[h.size()-2],p[i]-h.back())<=0)h.pop_back();h.push_back(p[i]);}
  h.pop_back(); return h;
}
double margin(const std::vector<V2>& points,V2 p){
  auto h=hull(points);if(h.size()<3)return -1.; double result=1e9;
  for(size_t i=0;i<h.size();++i){V2 e=h[(i+1)%h.size()]-h[i];result=std::min(result,cross(e,p-h[i])/e.norm());}return result;
}
bool unloaded(double fraction,double triangle,const std::array<V3,4>& f,double fr_clearance){
 return fraction<=.05&&triangle>=MARGIN&&f[0].z()>=CONTACT&&f[2].z()>=CONTACT&&f[3].z()>=CONTACT&&std::abs(fr_clearance)<=.002;
}
int main(int argc,char**argv){try{
 if(argc==2&&std::string(argv[1])=="--self-test"){
  std::vector<V2> t{{0,0},{1,0},{0,1}};
  if(std::abs(margin(t,{.2,.2})-.2)>1e-10||margin(t,{1,1})>=0||margin({{0,0},{1,1}},{0,0})>=0)throw std::runtime_error("polygon test");
  std::array<V3,4> f; for(auto&v:f)v=V3(0,0,10);
  if(!unloaded(.04,.002,f,0)||unloaded(.06,.002,f,0)||unloaded(.04,-.001,f,0)||unloaded(.04,.002,f,.005))throw std::runtime_error("unload gate test");
  for(int l=0;l<4;++l){auto leg=static_cast<lite3::Leg>(l);auto p=lite3::FootPositionBody(leg,STAND);auto ik=lite3::SolveFootIk(leg,p+V3(.002,-.002,0),STAND);if(!ik.converged||(lite3::FootPositionBody(leg,ik.q)-p-V3(.002,-.002,0)).norm()>1e-6)throw std::runtime_error("IK test");}
  std::cout<<"geometry and unload gates PASS\n";return 0;
 }
 std::map<std::string,std::string> a;
 for(int i=1;i<argc;i+=2){if(i+1>=argc)throw std::runtime_error("key needs value");a[argv[i]]=argv[i+1];}
 auto n=[&](std::string k,double d){return a.count(k)?std::stod(a[k]):d;};
 const double x=n("--x",0),y=n("--y",0),duration=n("--duration",4),lift=n("--lift",0),kp=n("--kp",100),kd=n("--kd",2.5);
 if(!std::isfinite(x+y+duration+lift+kp+kd)||duration<2||lift<0||lift>.005||kp<60||kp>100||kd<.7||kd>2.5)throw std::runtime_error("invalid simulation parameters");
 std::string prefix=a.at("--out");
 char err[2048]; mjModel*m=mj_loadXML(a.at("--model").c_str(),nullptr,err,sizeof err);if(!m)throw std::runtime_error(err);
 if(m->nq!=19||m->nv!=18||m->nu!=12)throw std::runtime_error("unexpected model dimensions");
 int torso=mj_name2id(m,mjOBJ_BODY,"TORSO"),floor=mj_name2id(m,mjOBJ_GEOM,"floor");
 std::array<int,4> feet;for(int l=0;l<4;++l)feet[l]=mj_name2id(m,mjOBJ_GEOM,(std::string(lite3::kLegNames[l])+"_FOOT_collision").c_str());
 std::ofstream audit(prefix+"_model.csv");audit<<"body,mass,com_x,com_y,com_z,Ixx,Iyy,Izz\n";
 std::ofstream settings(prefix+"_settings.json");settings<<"{\"solver\":"<<m->opt.solver<<",\"iterations\":"<<m->opt.iterations<<",\"tolerance\":"<<m->opt.tolerance<<",\"integrator\":"<<m->opt.integrator<<",\"cone\":"<<m->opt.cone<<",\"source_dt\":"<<m->opt.timestep<<",\"runtime_dt\":"<<DT<<",\"source_damping\":"<<m->dof_damping[6]<<",\"source_frictionloss\":"<<m->dof_frictionloss[6]<<",\"floor_solref\":["<<m->geom_solref[2*floor]<<','<<m->geom_solref[2*floor+1]<<"],\"foot_solimp\":[";for(int j=0;j<5;++j){if(j)settings<<',';settings<<m->geom_solimp[5*feet[0]+j];}settings<<"]}\n";
 for(int b=1;b<m->nbody;++b){audit<<mj_id2name(m,mjOBJ_BODY,b)<<','<<m->body_mass[b];for(int j=0;j<3;++j)audit<<','<<m->body_ipos[3*b+j];for(int j=0;j<3;++j)audit<<','<<m->body_inertia[3*b+j];audit<<'\n';}
 // Runtime perturbations affect a private model only. Added payload is a point
 // mass rigidly attached to the torso, combined with parallel-axis inertia.
 for(int b=1;b<m->nbody;++b){double scale=n("--mass",1)*n("--link"+std::to_string(b),1);m->body_mass[b]*=scale;for(int j=0;j<3;++j)m->body_inertia[3*b+j]*=scale;}
 double payload=n("--payload",0),oldmass=m->body_mass[torso];
 V3 oldcom(m->body_ipos+3*torso),payloadpos(n("--com-x",0),n("--com-y",0),n("--com-z",.10));
 V3 newcom=(oldmass*oldcom+payload*payloadpos)/(oldmass+payload);
 Eigen::Matrix3d inertia=Eigen::Matrix3d::Zero();
 mjtNum rotbuf[9];mju_quat2Mat(rotbuf,m->body_iquat+4*torso);
 Eigen::Map<Eigen::Matrix<double,3,3,Eigen::RowMajor>> rot(rotbuf);
 inertia=rot*V3(m->body_inertia+3*torso).asDiagonal()*rot.transpose();
 for(auto pair:std::vector<std::pair<double,V3>>{{oldmass,oldcom-newcom},{payload,payloadpos-newcom}})inertia+=pair.first*(pair.second.squaredNorm()*Eigen::Matrix3d::Identity()-pair.second*pair.second.transpose());
 Eigen::SelfAdjointEigenSolver<Eigen::Matrix3d> eig(inertia);Eigen::Matrix3d axes=eig.eigenvectors();if(axes.determinant()<0)axes.col(0)*=-1;
 Eigen::Quaterniond quat(axes);m->body_mass[torso]+=payload;
 for(int j=0;j<3;++j){m->body_ipos[3*torso+j]=newcom[j];m->body_inertia[3*torso+j]=eig.eigenvalues()[j];}
 m->body_iquat[4*torso]=quat.w();m->body_iquat[4*torso+1]=quat.x();m->body_iquat[4*torso+2]=quat.y();m->body_iquat[4*torso+3]=quat.z();
 // The compiler cached that the original torso inertial frame equals its
 // body frame. Invalidate that shortcut when runtime payload changes it.
 m->body_sameframe[torso]=0;
 for(int g=0;g<m->ngeom;++g){m->geom_friction[3*g]=n("--friction",1);m->geom_solref[2*g]*=n("--contact",1);
  const char*name=mj_id2name(m,mjOBJ_GEOM,g);if(n("--sphere-only",0)&&name&&std::string(name).find("_SHANK_collision")!=std::string::npos){m->geom_contype[g]=0;m->geom_conaffinity[g]=0;}}
 for(int j=6;j<m->nv;++j){m->dof_damping[j]=n("--damping",0);m->dof_frictionloss[j]=n("--joint-friction",0);}
 m->opt.timestep=DT;
 mjData*d=mj_makeData(m);mj_setConst(m,d);mj_resetData(m,d);
 d->qpos[2]=.022-lite3::FootPositionBody(lite3::Leg::FL,STAND).z();
 Eigen::Quaterniond initial(Eigen::AngleAxisd(n("--roll",0),V3::UnitX())*Eigen::AngleAxisd(n("--pitch",0),V3::UnitY()));
 d->qpos[3]=initial.w();d->qpos[4]=initial.x();d->qpos[5]=initial.y();d->qpos[6]=initial.z();
 Q qstand;for(int j=0;j<12;++j){qstand[j]=STAND[j%3];d->qpos[7+j]=qstand[j]+n("--qerr",0)*(j%2?1:-1);}
 mj_forward(m,d);
 V3 expected_com=V3(d->xpos+3*torso)+initial*newcom;
 if((V3(d->xipos+3*torso)-expected_com).norm()>1e-9)throw std::runtime_error("payload COM runtime update failed");
 double fk_error=0;for(int l=0;l<4;++l){V3 q(d->qpos+7+3*l),body=lite3::FootPositionBody(static_cast<lite3::Leg>(l),q);V3 world=V3(d->qpos)+initial*body;fk_error=std::max(fk_error,(world-V3(d->geom_xpos+3*feet[l])).norm());}
 if(fk_error>1e-6)throw std::runtime_error("FK does not match MJCF");
 std::ofstream log(prefix+".csv");log<<std::setprecision(10);
 log<<"time,phase,com_x,com_y,support_margin,triangle_margin,roll,pitch,yaw,wx,wy,wz,fr_fraction,fr_clearance,fr_fk_x,fr_fk_y,fr_fk_z,tracking,dq,target_delta,target_speed,target_acceleration,actual_acceleration,joint_limit_distance,friction_ratio,force_slew,nonfoot_fz,unload_verified";
 for(int l=0;l<4;++l)for(auto c:{"fx","fy","fz","contact_x","contact_y","contact_z","contact"})log<<','<<lite3::kLegNames[l]<<'_'<<c;
 for(int j=0;j<12;++j)log<<",q"<<j<<",target"<<j<<",dq"<<j<<",target_dq"<<j<<",ddq"<<j<<",target_ddq"<<j;
 for(int l=0;l<4;++l)for(int j=0;j<9;++j)log<<",J"<<l<<'_'<<j;
 log<<'\n';
 Q prev=qstand,prevvel=Q::Zero(),prevactual=Q::Zero();std::vector<Q> history;
 double maxdq=0,maxtrack=0,maxroll=0,maxpitch=0,maxdelta=0,maxspeed=0,maxacc=0,minmargin=1,mintri=1,minfrac=1,maxclear=0,maxfriction=0,maxslew=0,minlimit=1,maxactualacc=0;
 double baselinefrac=0,baselineweight=0;int baselinecount=0;
 std::array<double,4> baselineforces{};
 double unload_time=0,lift_time=0;bool verified=false,stand_ok=true,ok=true,plan_ok=true;std::string first="none";
 std::array<V3,4> lastforces;for(auto&v:lastforces)v.setZero();
 const double settle=3,hold=1,liftDuration=2,liftHold=.5;
 const double liftStart=settle+duration+hold,lowerStart=liftStart+liftDuration+liftHold,recenterStart=lift?lowerStart+liftDuration:liftStart;
 const double total=recenterStart+duration+1;
 for(int step=0;step<=int(total/DT);++step){
  double t=step*DT;std::string phase="SETTLE";double shift=0,z=0;
  if(t>=settle&&t<settle+duration){phase="SHIFT";shift=lite3::Quintic((t-settle)/duration);}
  else if(t>=settle+duration&&t<liftStart){phase="VERIFY_UNLOAD";shift=1;}
  else if(lift&&t>=liftStart&&t<lowerStart){phase=t<liftStart+liftDuration?"LIFT":"HOLD_LIFT";shift=1;if(verified)z=lift*lite3::Quintic((t-liftStart)/liftDuration);}
  else if(lift&&t>=lowerStart&&t<recenterStart){phase="LOWER";shift=1;if(verified)z=lift*(1-lite3::Quintic((t-lowerStart)/liftDuration));}
  else if(t>=recenterStart&&t<recenterStart+duration){phase="RECENTER";shift=1-lite3::Quintic((t-recenterStart)/duration);}
  else if(t>=recenterStart+duration)phase="FINAL";
  Q target;
  for(int l=0;l<4;++l){auto leg=static_cast<lite3::Leg>(l);V3 point=lite3::FootPositionBody(leg,STAND)+V3(-x*shift,-y*shift,l==1?z:0);auto ik=lite3::SolveFootIk(leg,point,prev.segment<3>(3*l));if(!ik.converged)throw std::runtime_error("IK failure");target.segment<3>(3*l)=ik.q;}
  Q vel=(target-prev)/DT,acc=(vel-prevvel)/DT;
  double delta=(target-qstand).cwiseAbs().maxCoeff(),speed=vel.cwiseAbs().maxCoeff();maxdelta=std::max(maxdelta,delta);maxspeed=std::max(maxspeed,speed);maxacc=std::max(maxacc,acc.cwiseAbs().maxCoeff());
  if(delta>DELTA+1e-6||speed>SPEED+1e-6){plan_ok=false;ok=false;if(first=="none")first="command_envelope";break;}
  Q measured(d->qpos+7),dq(d->qvel+6);history.push_back(measured);
  int delay=std::max(0,int(std::round(n("--delay",0)/DT)));Q sensed=history[std::max(0,int(history.size())-1-delay)];
  for(int j=0;j<12;++j)d->ctrl[j]=std::clamp(n("--strength",1)*(kp*(target[j]-sensed[j])+kd*(vel[j]-dq[j])),-30.,30.);
  // Evaluate contacts and state at the same time. mj_forward computes forces
  // for this control before mj_step advances the free base.
  mj_forward(m,d);
  std::array<V3,4> forces,positions;for(int l=0;l<4;++l){forces[l].setZero();positions[l]=V3(d->geom_xpos+3*feet[l]);positions[l].z()-=.022;}
  double friction=0,nonfoot=0;
  for(int c=0;c<d->ncon;++c){auto&contact=d->contact[c];if(contact.geom1!=floor&&contact.geom2!=floor)continue;
   int other=contact.geom1==floor?contact.geom2:contact.geom1; mjtNum wrench[6];mj_contactForce(m,d,c,wrench);
   Eigen::Map<Eigen::Matrix<double,3,3,Eigen::RowMajor>> frame(contact.frame);V3 world=frame.transpose()*V3(wrench);if(contact.geom2==floor)world=-world;
   int leg=-1;for(int l=0;l<4;++l)if(other==feet[l])leg=l;
   if(leg<0){nonfoot+=std::max(0.,world.z());continue;}forces[leg]+=world;positions[leg]=V3(contact.pos);
   if(wrench[0]>.1)friction=std::max(friction,std::hypot(wrench[1],wrench[2])/(contact.friction[0]*wrench[0]));
  }
  double sum=0,slew=0;std::vector<V2> support;for(int l=0;l<4;++l){sum+=forces[l].z();if(forces[l].z()>=CONTACT)support.push_back(positions[l].head<2>());slew=std::max(slew,std::abs(forces[l].z()-lastforces[l].z())/DT);}
  V2 com(d->subtree_com[3*torso],d->subtree_com[3*torso+1]);double sm=margin(support,com),tri=margin({positions[0].head<2>(),positions[2].head<2>(),positions[3].head<2>()},com),frac=sum>1?forces[1].z()/sum:1;
  double qw=d->qpos[3],qx=d->qpos[4],qy=d->qpos[5],qz=d->qpos[6];
  double roll=std::atan2(2*(qw*qx+qy*qz),1-2*(qx*qx+qy*qy)),pitch=std::asin(std::clamp(2*(qw*qy-qz*qx),-1.,1.)),yaw=std::atan2(2*(qw*qz+qx*qy),1-2*(qy*qy+qz*qz));
  double tracking=(target-measured).cwiseAbs().maxCoeff(),mdq=dq.cwiseAbs().maxCoeff(),clear=d->geom_xpos[3*feet[1]+2]-.022,jlimit=1;
  for(int j=0;j<12;++j)jlimit=std::min({jlimit,measured[j]-m->jnt_range[2*(j+1)],m->jnt_range[2*(j+1)+1]-measured[j]});
  double actualacc=((dq-prevactual)/DT).cwiseAbs().maxCoeff();
  bool finite=std::isfinite(sm+tri+frac+roll+pitch+tracking+mdq+clear);
  bool safe=finite&&std::abs(roll)<=ANGLE&&std::abs(pitch)<=ANGLE&&mdq<=MEASURED&&tracking<=TRACK&&sm>=0&&jlimit>.01&&friction<=1.05&&nonfoot<1;
  if(verified&&(phase=="LIFT"||phase=="HOLD_LIFT"||phase=="LOWER"))safe=safe&&tri>=MARGIN&&forces[0].z()>=CONTACT&&forces[2].z()>=CONTACT&&forces[3].z()>=CONTACT;
  if(phase=="FINAL"&&t>recenterStart+duration+.5)safe=safe&&support.size()==4;
  if(t>=settle-.5){
   if(!safe){ok=false;if(first=="none")first=!finite?"nonfinite":nonfoot>=1?"nonfoot_contact":sm<0?"support":std::abs(roll)>ANGLE||std::abs(pitch)>ANGLE?"attitude":mdq>MEASURED?"measured_speed":tracking>TRACK?"tracking":jlimit<=.01?"joint_limit":"friction";}
   maxdq=std::max(maxdq,mdq);maxtrack=std::max(maxtrack,tracking);maxroll=std::max(maxroll,std::abs(roll));maxpitch=std::max(maxpitch,std::abs(pitch));minmargin=std::min(minmargin,sm);maxfriction=std::max(maxfriction,friction);maxslew=std::max(maxslew,slew);minlimit=std::min(minlimit,jlimit);maxactualacc=std::max(maxactualacc,actualacc);
   if(t<settle){stand_ok=stand_ok&&safe&&support.size()==4;baselinefrac+=frac;baselineweight+=sum;for(int l=0;l<4;++l)baselineforces[l]+=forces[l].z();++baselinecount;}
  }
  if(phase=="VERIFY_UNLOAD"){
   mintri=std::min(mintri,tri);minfrac=std::min(minfrac,frac);
   if(safe&&unloaded(frac,tri,forces,clear))unload_time+=DT;else unload_time=0;
   // Require the last continuous 0.5 s immediately before lift, not any
   // earlier transient. A prior safety failure permanently invalidates it.
   verified=unload_time>=.5&&ok&&stand_ok;
  }
  if(phase=="HOLD_LIFT"){
   maxclear=std::max(maxclear,clear);
   if(verified&&safe&&tri>=MARGIN&&clear>=.003&&forces[1].z()<1&&forces[0].z()>=CONTACT&&forces[2].z()>=CONTACT&&forces[3].z()>=CONTACT)lift_time+=DT;else lift_time=0;
  }
  if(step%10==0){V3 frfk=lite3::FootPositionBody(lite3::Leg::FR,measured.segment<3>(3));
   log<<t<<','<<phase<<','<<com.x()<<','<<com.y()<<','<<sm<<','<<tri<<','<<roll<<','<<pitch<<','<<yaw<<','<<d->qvel[3]<<','<<d->qvel[4]<<','<<d->qvel[5]<<','<<frac<<','<<clear<<','<<frfk.x()<<','<<frfk.y()<<','<<frfk.z()<<','<<tracking<<','<<mdq<<','<<delta<<','<<speed<<','<<acc.cwiseAbs().maxCoeff()<<','<<actualacc<<','<<jlimit<<','<<friction<<','<<slew<<','<<nonfoot<<','<<verified;
   for(int l=0;l<4;++l){for(int j=0;j<3;++j)log<<','<<forces[l][j];for(int j=0;j<3;++j)log<<','<<positions[l][j];log<<','<<(forces[l].z()>=CONTACT);}
   for(int j=0;j<12;++j)log<<','<<measured[j]<<','<<target[j]<<','<<dq[j]<<','<<vel[j]<<','<<(dq[j]-prevactual[j])/DT<<','<<acc[j];
   for(int l=0;l<4;++l){auto J=lite3::NumericalJacobian(static_cast<lite3::Leg>(l),measured.segment<3>(3*l));for(int r=0;r<3;++r)for(int c=0;c<3;++c)log<<','<<J(r,c);}
   log<<'\n';
  }
  prev=target;prevvel=vel;prevactual=dq;lastforces=forces;mj_step(m,d);
 }
 std::ofstream out(prefix+".json");out<<std::setprecision(12)<<"{\n";
 auto field=[&](const char*key,double value){out<<'"'<<key<<"\":"<<value<<",\n";};
 field("stand_pass",stand_ok&&baselinecount>0);field("plan_pass",plan_ok);field("safe",ok);field("unload_pass",verified&&ok&&plan_ok);field("lift_pass",lift>0&&verified&&ok&&lift_time>=.49);field("lift_requested",lift>0);field("fr_fraction_stand",baselinecount?baselinefrac/baselinecount:1);field("weight_stand_n",baselinecount?baselineweight/baselinecount:0);
 for(int l=0;l<4;++l)field((std::string(lite3::kLegNames[l])+"_stand_fz").c_str(),baselinecount?baselineforces[l]/baselinecount:0);
 field("min_fr_fraction",minfrac);field("min_support_margin_m",minmargin);field("min_triangle_margin_verify_m",mintri);field("max_roll_rad",maxroll);field("max_pitch_rad",maxpitch);field("max_tracking_rad",maxtrack);field("max_dq_rad_s",maxdq);field("max_target_delta_rad",maxdelta);field("max_target_speed_rad_s",maxspeed);field("max_target_acceleration_rad_s2",maxacc);field("max_actual_acceleration_rad_s2",maxactualacc);field("min_joint_limit_distance_rad",minlimit);field("max_friction_ratio",maxfriction);field("max_force_slew_n_s",maxslew);field("fr_lift_clearance_m",maxclear);field("fk_error_m",fk_error);
 out<<"\"first_failure\":\""<<first<<"\"}\n";
 mj_deleteData(d);mj_deleteModel(m);return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
