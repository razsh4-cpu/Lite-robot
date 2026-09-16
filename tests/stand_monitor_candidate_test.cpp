#include "stand_monitor_candidate.hpp"
#include <iostream>
#include <stdexcept>
using namespace stand_candidate;
int count=0;
void ExpectAt(bool value,int line) { ++count; if(!value) throw std::runtime_error("monitor assertion #"+std::to_string(count)+" line "+std::to_string(line)); }
#define Expect(value) ExpectAt((value),__LINE__)
static Sample Ready() { Sample s;s.fresh=s.target_valid=s.final_target=true;return s; }
static Result Feed(Monitor& m,Sample& s,int first,int last) {
    Result r=Result::StandingUp;
    for(int i=first;i<=last;++i) {r=m.Check(i*.001,s);if(r==Result::Abort)break;}
    return r;
}
int main() {
    try {
        auto s=Ready(); Monitor m;
        Expect(m.Check(0,s)==Result::Abort);
        m.Start(0); s.final_target=false;
        Expect(Feed(m,s,1,3000)==Result::StandingUp);
        s.final_target=true;
        Expect(Feed(m,s,3001,3499)==Result::StandingUp);
        Expect(Feed(m,s,3500,3502)==Result::TargetReached);
        Expect(Feed(m,s,3503,9000)==Result::TargetReached);
        Expect(m.Check(9.001,s,true)==Result::Abort);

        // Isolated spikes can pass the approved window, sustained speed cannot.
        m.Start(0); s=Ready();
        Expect(Feed(m,s,1,600)==Result::TargetReached);
        s.velocity[9]=.22;
        Expect(m.Check(.601,s)==Result::TargetReached);
        Expect(m.diagnostics().raw_max_speed==.22 && m.diagnostics().rms_max_speed<.15);
        s.velocity[9]=0; Expect(Feed(m,s,602,700)==Result::TargetReached);
        s.velocity[9]=.2;
        Expect(Feed(m,s,701,775)==Result::TargetReached);
        Expect(Feed(m,s,776,840)==Result::Abort);
        Expect(std::string(m.reason())=="persistent velocity convergence loss");

        // Hardware trace fingerprint: four high dq samples over ~4.1 ms on
        // FR HipY, but essentially fixed position/attitude. The RMS crosses
        // 0.15 for one sample only, then recovers: established hold must remain.
        m.Start(0);s=Ready();Expect(Feed(m,s,1,600)==Result::TargetReached);
        const double traced[]={-.453911,-.128822,.584679,.569878,.356636,.142632};
        for(int k=0;k<6;++k) {
            s.velocity[4]=traced[k];
            s.position[4]+=(k==0?-.00023:(k==1?-.00061:(k==2?.00031:(k==3?.00015:0))));
            Expect(m.Check(.601+k*.0011,s)==Result::TargetReached);
        }
        s.velocity[4]=0;
        Expect(Feed(m,s,608,720)==Result::TargetReached);
        Expect(std::string(m.reason())=="target reached");

        // Latest live trace fingerprint: an approximately 5 ms HR-knee burst
        // leaves the 50 ms RMS above 0.15 after raw velocity has settled. It is
        // transient, not a persistent hold loss, and must age out without an
        // abort. Position and attitude remain within their independent guards.
        m.Start(0);s=Ready();Expect(Feed(m,s,1,600)==Result::TargetReached);
        const double hr_knee_trace[]={.3724,.9482,1.2786,1.0307,.3946,.0684};
        const double hr_knee_position[]={0,.0004,.0011,.0017,.0019,.0019};
        for(int k=0;k<6;++k) {
            s.velocity[11]=hr_knee_trace[k];
            s.position[11]=hr_knee_position[k];
            Expect(m.Check(.601+k*.00105,s)==Result::TargetReached);
        }
        s.velocity[11]=0;
        Expect(Feed(m,s,608,760)==Result::TargetReached);
        Expect(std::string(m.reason())=="target reached");

        m.Start(0);s=Ready();s.velocity[1]=.16;
        Expect(Feed(m,s,1,5900)==Result::StandingUp);
        Expect(m.Check(6,s)==Result::Abort);
        Expect(std::string(m.reason())=="convergence deadline");
        // RMS must not cancel opposite signs.
        m.Start(0);s=Ready();
        for(int i=1;i<=1000;++i) {s.velocity[2]=(i%2?.2:-.2);Expect(m.Check(i*.001,s)==Result::StandingUp);}
        Expect(m.diagnostics().rms_max_speed>.19);
        // Position range detects movement even if velocity feedback falsely reads zero.
        m.Start(0);s=Ready();
        for(int i=1;i<=1000;++i) {
            s.position[0]=.02*std::sin(i*.001*2*3.141592653589793*10);
            Expect(m.Check(i*.001,s)==Result::StandingUp);
        }
        Expect(m.diagnostics().position_range_speed>.15);

        // Gaps and non-progressing samples cannot fill the window or dwell.
        m.Start(0);s=Ready();Expect(Feed(m,s,1,400)==Result::StandingUp);
        Expect(m.Check(.46,s)==Result::StandingUp);
        Expect(!m.diagnostics().speed_window_ready && m.diagnostics().dwell_elapsed==0);
        s.new_feedback=false;
        Expect(Feed(m,s,461,900)==Result::StandingUp);
        Expect(m.diagnostics().dwell_elapsed==0);
        s.new_feedback=true;
        Expect(Feed(m,s,901,1400)==Result::StandingUp);
        Expect(Feed(m,s,1401,1455)==Result::TargetReached);
        m.Start(0);s=Ready();
        for(int i=0;i<1000;++i) Expect(m.Check(.001,s)==Result::StandingUp);
        Expect(!m.diagnostics().speed_window_ready);
        m.Start(0);s=Ready();
        for(int i=1;i<600;++i) Expect(m.Check(i*.000001,s)==Result::StandingUp);
        Expect(!m.diagnostics().speed_window_ready); // capacity fails closed

        // Raw guards still abort immediately, including invalid/overflow inputs.
        for(int failure=0;failure<8;++failure) {
            m.Start(0);s=Ready();Expect(Feed(m,s,1,600)==Result::TargetReached);
            if(failure==0)s.position[0]=.36;
            if(failure==1)s.roll=.36;
            if(failure==2)s.pitch=std::numeric_limits<double>::quiet_NaN();
            if(failure==3)s.fresh=false;
            if(failure==4)s.velocity[0]=std::numeric_limits<double>::infinity();
            if(failure==5)s.target[0]=std::numeric_limits<double>::infinity();
            if(failure==6)s.velocity[0]=1e300;
            Expect(m.Check(.601,s,failure==7)==Result::Abort);
        }
        m.Start(0);s=Ready();Expect(m.Check(.1,s)==Result::StandingUp);
        Expect(m.Check(.09,s)==Result::Abort);
        std::cout<<"PASS: "<<count<<" focused window/guard checks; no SDK/network\n";
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; return 1; }
}
