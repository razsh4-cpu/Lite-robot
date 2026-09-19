#include "state_machine/supported_body_shift_plan.hpp"
#include <cmath>
#include <iostream>
#include <stdexcept>

namespace { void Check(bool ok,const char* why) { if(!ok) throw std::runtime_error(why); } }
int main() {
  try {
    for (const auto strategy : {SupportedBodyShiftPlan::GainStrategy::AbruptReduced,
                                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                                SupportedBodyShiftPlan::GainStrategy::SmoothReduced}) {
      SupportedBodyShiftPlan plan(strategy); double max_delta=0,max_speed=0;
      for(int n=0;n<=5000;++n) { const auto sample=plan.At(n*.001); Check(sample.command.allFinite(),"finite command");
        for(int i=0;i<12;++i) { const auto q0=plan.stand()[i/3][i%3]; max_delta=std::max(max_delta,std::abs(double(sample.command(i,1))-q0)); max_speed=std::max(max_speed,std::abs(double(sample.command(i,3))));
          Check(sample.command(i,4)==0.0f,"zero feed-forward torque"); Check(sample.command(i,0)>=0 && sample.command(i,0)<=100,"bounded kp"); Check(sample.command(i,2)>=0 && sample.command(i,2)<=2.5,"bounded kd"); }
      }
      std::cout << "MEASURED max_delta=" << max_delta
                << " rad  max_speed=" << max_speed
                << " rad/s  limits: delta="
                << SupportedBodyShiftPlan::kMaxJointDeltaRad
                << " speed="
                << SupportedBodyShiftPlan::kMaxTargetSpeedRadS
                << "\n";
      Check(max_delta <= SupportedBodyShiftPlan::kMaxJointDeltaRad + 1e-7,"target delta limit");
      Check(max_speed <= SupportedBodyShiftPlan::kMaxTargetSpeedRadS + 1e-7,"target speed limit");
      const auto done=plan.At(SupportedBodyShiftPlan::kTotalSeconds+.001); Check(done.complete,"plan completes");
      std::cout<<"body_shift strategy="<<static_cast<int>(strategy)<<" max_delta="<<max_delta<<" max_speed="<<max_speed<<"\n";
    }
    SupportedBodyShiftPlan smooth(SupportedBodyShiftPlan::GainStrategy::SmoothReduced);
    Check(smooth.At(0).command(0,0)==SupportedBodyShiftPlan::kStandKp,"smooth starts at stand kp");
    Check(std::abs(smooth.At(SupportedBodyShiftPlan::kGainRampSeconds).command(0,0)-SupportedBodyShiftPlan::kReducedKp)<1e-5,"smooth reaches reduced kp");
    std::cout<<"supported body-shift plan: PASS\n"; return 0;
  } catch(const std::exception& e) { std::cerr<<"supported body-shift plan: FAIL: "<<e.what()<<"\n"; return 1; }
}
