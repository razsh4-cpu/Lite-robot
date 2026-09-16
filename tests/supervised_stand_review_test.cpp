#include "supervised_stand_review_model.hpp"
#include <iostream>
#include <stdexcept>
#include <string>
using namespace stand_review;
int checks=0;
void Check(bool ok,const char* message) {
    ++checks; if(!ok) throw std::runtime_error(message);
}
Conditions Healthy() {
    Conditions c;
    c.acquisition_session=1; c.acquisition_requested=true;
    c.feedback_fresh=true; c.passive_health_reviewed=true;
    c.estop_ready=true; c.operator_present=true;
    c.normalized_velocity_zero=true; c.joint_gate_closed=true;
    return c;
}
Authorization Active(Conditions& c) {
    Authorization a;
    Check(a.authorize_once(0,c),"arm valid session");
    Check(!a.permit_stand_output(0,c,Controller::Stand,true),"armed cannot send");
    Check(a.request_stand(1,c),"queue stand");
    Check(!a.permit_stand_output(1,c,Controller::Stand,true),"pending cannot send");
    c.controller=Controller::Stand;
    Check(a.entered_stand(2,c),"entry authorizes stand only");
    c.joint_gate_closed=false;
    return a;
}
int main() {
    try {
        auto c=Healthy(); Authorization a;
        Check(!a.request_stand(0,c),"default stand blocked");
        Check(!a.permit_stand_output(0,c,Controller::Stand,true),"default output blocked");
        Check(!a.request_rl() && !a.permit_nonzero_velocity(),"RL/motion always blocked");
        Check(std::string(a.ownership())=="OWNERSHIP_UNCONFIRMED","honest ownership");
        for(auto member : {&Conditions::acquisition_requested,&Conditions::feedback_fresh,
                           &Conditions::passive_health_reviewed,&Conditions::estop_ready,
                           &Conditions::operator_present,&Conditions::normalized_velocity_zero,
                           &Conditions::joint_gate_closed}) {
            auto bad=Healthy(); bad.*member=false; Authorization denied;
            Check(!denied.authorize_once(0,bad),"missing precondition must block arm");
        }
        auto zero_session=Healthy(); zero_session.acquisition_session=0;
        Check(!a.authorize_once(0,zero_session),"no acquisition epoch blocks arm");
        Check(a.authorize_once(0,c),"explicit arm accepted");
        Check(!a.authorize_once(4000,c),"duplicate does not extend deadline");
        Check(!a.request_stand(5000,c),"deadline expires at boundary");
        Check(!a.authorize_once(5001,c),"expired token cannot be rearmed in same session");
        Check(!a.begin_new_acquisition_session(1),"old acquisition ID rejected");
        Check(a.begin_new_acquisition_session(2),"new explicit session may start locked");
        Check(!a.authorize_once(5001,c),"old session cannot replace new acquisition epoch");
        c.acquisition_session=2;
        Check(!a.request_stand(5001,c),"new session requires new authorization");
        Check(a.authorize_once(5001,c),"new explicit authorization");
        c.acquisition_session=3;
        Check(!a.request_stand(5002,c),"session mismatch invalidates token");
        c=Healthy(); auto active=Active(c);
        Check(active.permit_stand_output(3,c,Controller::Stand,true),"only stand producer allowed");
        Check(!active.request_stand(3,c),"one request per grant");
        Check(!active.request_rl() && !active.permit_nonzero_velocity(),"active grant is not locomotion");
        Check(std::string(active.ownership())=="OWNERSHIP_UNCONFIRMED","arm never confirms ownership");
        Check(!active.permit_stand_output(10002,c,Controller::Stand,true),"active deadline enforced");
        for(auto producer : {Controller::Idle,Controller::RL,Controller::Damping}) {
            c=Healthy(); auto x=Active(c);
            Check(!x.permit_stand_output(3,c,producer,true),"wrong producer rejected");
            Check(x.phase()==Phase::Revoked,"wrong producer revokes");
        }
        for(auto member : {&Conditions::acquisition_requested,&Conditions::feedback_fresh,
                           &Conditions::passive_health_reviewed,&Conditions::estop_ready,
                           &Conditions::operator_present,&Conditions::normalized_velocity_zero}) {
            c=Healthy(); auto x=Active(c); c.*member=false;
            Check(!x.permit_stand_output(3,c,Controller::Stand,true),"safety loss revokes output");
            c.*member=true;
            Check(!x.permit_stand_output(4,c,Controller::Stand,true),"recovery cannot auto-resume");
        }
        c=Healthy(); auto invalid=Active(c);
        Check(!invalid.permit_stand_output(3,c,Controller::Stand,false),"nonfinite joints rejected");
        c=Healthy(); auto stopped=Active(c); stopped.revoke();
        Check(!stopped.permit_stand_output(3,c,Controller::Stand,true),"stop/release/shutdown revoke");
        Check(!stopped.authorize_once(3,c),"revoked grant cannot be reused");
        std::cout<<"PASS: "<<checks<<" offline authorization-model checks; no SDK/socket imports\n";
    } catch(const std::exception& e) { std::cerr<<"FAIL: "<<e.what()<<'\n'; return 1; }
}
