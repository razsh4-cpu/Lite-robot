#include "state_machine/supported_body_shift_plan.hpp"

#include <cmath>
#include <iomanip>
#include <iostream>
#include <set>
#include <stdexcept>

namespace {
void Check(bool ok,const char* why) {
    if(!ok) throw std::runtime_error(why);
}
}

int main() {
    try {
        SupportedBodyShiftPlan exact(
            SupportedBodyShiftPlan::GainStrategy::KeepStand);
        std::cout << std::setprecision(12);
        std::cout << "SAFE_SCALE " << exact.safe_scale()
                  << " LIMITING_JOINT " << exact.limiting_joint()
                  << " DELTA " << exact.limiting_delta() << '\n';
        std::cout << "SAFE_TARGET";
        for(const auto& q:exact.safe_target())
            for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
        std::cout << '\n';
        Check(std::abs(exact.safe_scale()-0.229671278476)<1e-10,
              "maximum safe scale regression");
        Check(exact.limiting_joint()==4,
              "FR HipY is the limiting joint");
        Check(exact.limiting_delta()<=
              SupportedBodyShiftPlan::kMaxJointDeltaRad,
              "safe-scale boundary respects delta limit");
        const std::array<std::array<double,12>,3> expected_targets{{
            {{0.00610376407178,-0.768472375136,1.50465779227,
              0.00609168528231,-0.764054446902,1.49615874976,
              0.00610376407178,-0.768472375136,1.50465779227,
              0.00609168528231,-0.764054446902,1.49615874976}},
            {{0.0122192258066,-0.763848134681,1.50863894879,
              0.0121709117741,-0.755064853996,1.49164037797,
              0.0122192258066,-0.763848134681,1.50863894879,
              0.0121709117740,-0.755064853995,1.49164037797}},
            {{0.0183459064330,-0.759107611359,1.51244331741,
              0.0182373862950,-0.746011302851,1.48694428961,
              0.0183459064330,-0.759107611359,1.51244331741,
              0.0182373862950,-0.746011302851,1.48694428961}}
        }};

        for(int level=0;level<3;++level) {
            std::cout << "TARGET "
                      << SupportedBodyShiftPlan::kSafeFractions[level]
                      << " SCALE " << exact.scale(level);
            for(int leg=0;leg<4;++leg) {
                const auto& q=exact.target(level)[leg];
                for(int joint=0;joint<3;++joint) {
                    std::cout << ' ' << q[joint];
                    Check(std::abs(q[joint]-
                        expected_targets[level][3*leg+joint])<1e-10,
                        "exact safe calibration target regression");
                }

                const auto nominal=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),exact.stand()[leg]);
                const auto shifted=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),q);
                const Eigen::Vector3d expected(
                    -exact.scale(level)*
                        SupportedBodyShiftPlan::kReferenceShiftXM,
                    -exact.scale(level)*
                        SupportedBodyShiftPlan::kReferenceShiftYM,
                    0.0);
                Check((shifted-nominal-expected).norm()<5e-6,
                      "IK target matches scaled Cartesian body shift");
                Check(std::abs(shifted.z()-nominal.z())<5e-6,
                      "body-only target keeps foot height unchanged");
            }
            double level_delta=0.0;
            for(int joint=0;joint<12;++joint)
                level_delta=std::max(level_delta,std::abs(
                    exact.target(level)[joint/3][joint%3]-
                    exact.stand()[joint/3][joint%3]));
            const double level_speed=1.875*level_delta/
                SupportedBodyShiftPlan::kShiftSeconds;
            std::cout << " MAX_DELTA " << level_delta
                      << " MAX_TARGET_SPEED " << level_speed << '\n';
            Check(level_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad,
                  "calibration level delta bound");
            Check(level_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS,
                  "calibration level speed bound");
        }

        for(const auto strategy : {
                SupportedBodyShiftPlan::GainStrategy::AbruptReduced,
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                SupportedBodyShiftPlan::GainStrategy::SmoothReduced}) {
            SupportedBodyShiftPlan plan(strategy);
            double max_delta=0.0,max_speed=0.0;
            std::set<SupportedBodyShiftPlan::Phase> phases;
            const int samples=static_cast<int>(
                SupportedBodyShiftPlan::kTotalSeconds*1000.0)+2;

            for(int n=0;n<=samples;++n) {
                const auto sample=plan.At(n*.001);
                phases.insert(sample.phase);
                Check(sample.command.allFinite(),"finite command");
                for(int i=0;i<12;++i) {
                    const auto q0=plan.stand()[i/3][i%3];
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(i,1))-q0));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(i,3))));
                    Check(sample.command(i,4)==0.0f,
                          "zero feed-forward torque");
                    Check(sample.command(i,0)>=0 && sample.command(i,0)<=100,
                          "bounded kp");
                    Check(sample.command(i,2)>=0 && sample.command(i,2)<=2.5,
                          "bounded kd");
                }
            }

            Check(phases.size()==13,"all calibration phases sampled");
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "target delta limit");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "target speed limit");
            Check(plan.At(SupportedBodyShiftPlan::kTotalSeconds+.001).complete,
                  "plan completes recentered");
            const auto done=plan.At(SupportedBodyShiftPlan::kTotalSeconds+.001);
            for(int i=0;i<12;++i)
                Check(std::abs(done.command(i,1)-plan.stand()[i/3][i%3])<1e-7,
                      "complete pose is nominal stand");

            std::cout << "MEASURED strategy=" << static_cast<int>(strategy)
                      << " max_delta=" << max_delta
                      << " max_speed=" << max_speed << '\n';
        }

        const std::array<SupportedBodyShiftPlan::RunMode,3> single_modes{{
            SupportedBodyShiftPlan::RunMode::Level30Only,
            SupportedBodyShiftPlan::RunMode::Level60Only,
            SupportedBodyShiftPlan::RunMode::Level90Only}};
        const std::array<SupportedBodyShiftPlan::Phase,3> single_settle{{
            SupportedBodyShiftPlan::Phase::Settle30,
            SupportedBodyShiftPlan::Phase::Settle60,
            SupportedBodyShiftPlan::Phase::Settle90}};
        const std::array<SupportedBodyShiftPlan::Phase,3> single_shift{{
            SupportedBodyShiftPlan::Phase::Shift30,
            SupportedBodyShiftPlan::Phase::Shift60,
            SupportedBodyShiftPlan::Phase::Shift90}};
        const std::array<SupportedBodyShiftPlan::Phase,3> single_hold{{
            SupportedBodyShiftPlan::Phase::Hold30,
            SupportedBodyShiftPlan::Phase::Hold60,
            SupportedBodyShiftPlan::Phase::Hold90}};
        const std::array<SupportedBodyShiftPlan::Phase,3> single_recenter{{
            SupportedBodyShiftPlan::Phase::Recenter30,
            SupportedBodyShiftPlan::Phase::Recenter60,
            SupportedBodyShiftPlan::Phase::Recenter90}};
        for(int level=0;level<3;++level) {
            SupportedBodyShiftPlan single(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                single_modes[level]);
            Check(single.total_seconds()==SupportedBodyShiftPlan::kLevelSeconds,
                  "single-level duration is bounded to one level");
            std::set<SupportedBodyShiftPlan::Phase> phases;
            for(int n=0;n<=static_cast<int>(single.total_seconds()*1000)+2;++n)
                phases.insert(single.At(n*.001).phase);
            Check(phases.size()==5 && phases.count(single_settle[level]) &&
                  phases.count(single_shift[level]) &&
                  phases.count(single_hold[level]) &&
                  phases.count(single_recenter[level]) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Complete),
                  "single-level mode contains only selected phases plus complete");
            Check(single.At(single.total_seconds()+.001).complete,
                  "single-level mode completes recentered");
        }

        {
            SupportedBodyShiftPlan reverse(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                SupportedBodyShiftPlan::RunMode::Level30ReverseYOnly);
            std::set<SupportedBodyShiftPlan::Phase> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(reverse.total_seconds()*1000)+2;++n) {
                const auto sample=reverse.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        reverse.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                    Check(sample.command(joint,4)==0.0f,
                          "reverse-Y feed-forward torque remains zero");
                }
            }
            Check(phases.size()==5 &&
                  phases.count(SupportedBodyShiftPlan::Phase::Settle30ReverseY) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Shift30ReverseY) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Hold30ReverseY) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Recenter30ReverseY) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Complete),
                  "reverse-Y mode contains only selected body-shift phases");
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "reverse-Y target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "reverse-Y target speed limit unchanged");
            for(int leg=0;leg<4;++leg) {
                const auto nominal=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),reverse.stand()[leg]);
                const auto shifted=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),reverse.reverse_y_target()[leg]);
                const Eigen::Vector3d body_translation(
                    reverse.scale(0)*SupportedBodyShiftPlan::kReferenceShiftXM,
                    -reverse.scale(0)*SupportedBodyShiftPlan::kReferenceShiftYM,
                    0.0);
                Check((shifted-nominal+body_translation).norm()<5e-6,
                      "reverse-Y IK preserves X and reverses only body Y");
                Check(std::abs(shifted.z()-nominal.z())<5e-6,
                      "reverse-Y mode keeps every foot at nominal height");
            }
            std::cout << "REVERSE_Y_TARGET";
            for(const auto& q:reverse.reverse_y_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            SupportedBodyShiftPlan refined(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                SupportedBodyShiftPlan::RunMode::Level30RefinedXOnly);
            std::set<SupportedBodyShiftPlan::Phase> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(refined.total_seconds()*1000)+2;++n) {
                const auto sample=refined.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        refined.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                    Check(sample.command(joint,4)==0.0f,
                          "refined-X feed-forward torque remains zero");
                }
            }
            Check(phases.size()==5 &&
                  phases.count(SupportedBodyShiftPlan::Phase::Settle30RefinedX) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Shift30RefinedX) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Hold30RefinedX) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Recenter30RefinedX) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Complete),
                  "refined-X mode contains only body-shift phases");
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "refined-X target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "refined-X target speed limit unchanged");
            for(int leg=0;leg<4;++leg) {
                const auto nominal=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),refined.stand()[leg]);
                const auto shifted=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),refined.refined_x_target()[leg]);
                const Eigen::Vector3d translation(
                    SupportedBodyShiftPlan::kRefinedShiftXM,
                    SupportedBodyShiftPlan::kRefinedShiftYM,0.0);
                Check((shifted-nominal+translation).norm()<5e-6,
                      "refined-X IK uses exact selected X/Y");
                Check(std::abs(shifted.z()-nominal.z())<5e-6,
                      "refined-X keeps every foot at nominal height");
            }
            std::cout << "REFINED_X_TARGET";
            for(const auto& q:refined.refined_x_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            SupportedBodyShiftPlan zero_x(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                SupportedBodyShiftPlan::RunMode::Level30ZeroXOnly);
            std::set<SupportedBodyShiftPlan::Phase> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(zero_x.total_seconds()*1000)+2;++n) {
                const auto sample=zero_x.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        zero_x.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                    Check(sample.command(joint,4)==0.0f,
                          "zero-X feed-forward torque remains zero");
                }
            }
            Check(phases.size()==5 &&
                  phases.count(SupportedBodyShiftPlan::Phase::Settle30ZeroX) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Shift30ZeroX) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Hold30ZeroX) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Recenter30ZeroX) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Complete),
                  "zero-X mode contains only body-shift phases");
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "zero-X target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "zero-X target speed limit unchanged");
            for(int leg=0;leg<4;++leg) {
                const auto nominal=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),zero_x.stand()[leg]);
                const auto shifted=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),zero_x.zero_x_target()[leg]);
                const Eigen::Vector3d translation(
                    SupportedBodyShiftPlan::kZeroXShiftXM,
                    SupportedBodyShiftPlan::kZeroXShiftYM,0.0);
                Check((shifted-nominal+translation).norm()<5e-6,
                      "zero-X IK uses exact selected X/Y");
                Check(std::abs(shifted.z()-nominal.z())<5e-6,
                      "zero-X keeps every foot at nominal height");
            }
            std::cout << "ZERO_X_TARGET";
            for(const auto& q:zero_x.zero_x_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            SupportedBodyShiftPlan y5(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                SupportedBodyShiftPlan::RunMode::LevelY5Only);
            std::set<SupportedBodyShiftPlan::Phase> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(y5.total_seconds()*1000)+2;++n) {
                const auto sample=y5.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        y5.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                    Check(sample.command(joint,4)==0.0f,
                          "Y5 feed-forward torque remains zero");
                }
            }
            Check(phases.size()==5 &&
                  phases.count(SupportedBodyShiftPlan::Phase::SettleY5) &&
                  phases.count(SupportedBodyShiftPlan::Phase::ShiftY5) &&
                  phases.count(SupportedBodyShiftPlan::Phase::HoldY5) &&
                  phases.count(SupportedBodyShiftPlan::Phase::RecenterY5) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Complete),
                  "Y5 mode contains only body-shift phases");
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "Y5 target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "Y5 target speed limit unchanged");
            for(int leg=0;leg<4;++leg) {
                const auto nominal=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),y5.stand()[leg]);
                const auto shifted=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),y5.y5_target()[leg]);
                const Eigen::Vector3d translation(
                    SupportedBodyShiftPlan::kY5ShiftXM,
                    SupportedBodyShiftPlan::kY5ShiftYM,0.0);
                Check((shifted-nominal+translation).norm()<5e-6,
                      "Y5 IK uses exact selected X/Y");
                Check(std::abs(shifted.z()-nominal.z())<5e-6,
                      "Y5 keeps every foot at nominal height");
            }
            std::cout << "Y5_TARGET";
            for(const auto& q:y5.y5_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            SupportedBodyShiftPlan y65(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                SupportedBodyShiftPlan::RunMode::LevelY65Only);
            std::set<SupportedBodyShiftPlan::Phase> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(y65.total_seconds()*1000)+2;++n) {
                const auto sample=y65.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        y65.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                    Check(sample.command(joint,4)==0.0f,
                          "Y65 feed-forward torque remains zero");
                }
            }
            Check(phases.size()==5 &&
                  phases.count(SupportedBodyShiftPlan::Phase::SettleY65) &&
                  phases.count(SupportedBodyShiftPlan::Phase::ShiftY65) &&
                  phases.count(SupportedBodyShiftPlan::Phase::HoldY65) &&
                  phases.count(SupportedBodyShiftPlan::Phase::RecenterY65) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Complete),
                  "Y65 mode contains only body-shift phases");
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "Y65 target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "Y65 target speed limit unchanged");
            for(int leg=0;leg<4;++leg) {
                const auto nominal=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),y65.stand()[leg]);
                const auto shifted=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),y65.y65_target()[leg]);
                const Eigen::Vector3d translation(
                    SupportedBodyShiftPlan::kY65ShiftXM,
                    SupportedBodyShiftPlan::kY65ShiftYM,0.0);
                Check((shifted-nominal+translation).norm()<5e-6,
                      "Y65 IK uses exact selected X/Y");
                Check(std::abs(shifted.z()-nominal.z())<5e-6,
                      "Y65 keeps every foot at nominal height");
            }
            std::cout << "Y65_TARGET";
            for(const auto& q:y65.y65_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            SupportedBodyShiftPlan x4y5(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                SupportedBodyShiftPlan::RunMode::LevelX4Y5Only);
            std::set<SupportedBodyShiftPlan::Phase> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(x4y5.total_seconds()*1000)+2;++n) {
                const auto sample=x4y5.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        x4y5.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                    Check(sample.command(joint,4)==0.0f,
                          "X4Y5 feed-forward torque remains zero");
                }
            }
            Check(phases.size()==5 &&
                  phases.count(SupportedBodyShiftPlan::Phase::SettleX4Y5) &&
                  phases.count(SupportedBodyShiftPlan::Phase::ShiftX4Y5) &&
                  phases.count(SupportedBodyShiftPlan::Phase::HoldX4Y5) &&
                  phases.count(SupportedBodyShiftPlan::Phase::RecenterX4Y5) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Complete),
                  "X4Y5 mode contains only body-shift phases");
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "X4Y5 target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "X4Y5 target speed limit unchanged");
            for(int leg=0;leg<4;++leg) {
                const auto nominal=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),x4y5.stand()[leg]);
                const auto shifted=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),x4y5.x4y5_target()[leg]);
                const Eigen::Vector3d translation(
                    SupportedBodyShiftPlan::kX4Y5ShiftXM,
                    SupportedBodyShiftPlan::kX4Y5ShiftYM,0.0);
                Check((shifted-nominal+translation).norm()<5e-6,
                      "X4Y5 IK uses exact selected X/Y");
                Check(std::abs(shifted.z()-nominal.z())<5e-6,
                      "X4Y5 keeps every foot at nominal height");
            }
            std::cout << "X4Y5_TARGET";
            for(const auto& q:x4y5.x4y5_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            SupportedBodyShiftPlan roll025(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                SupportedBodyShiftPlan::RunMode::LevelX2Y5Roll025Only);
            std::set<SupportedBodyShiftPlan::Phase> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(roll025.total_seconds()*1000)+2;++n) {
                const auto sample=roll025.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        roll025.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                    Check(sample.command(joint,4)==0.0f,
                          "roll025 feed-forward torque remains zero");
                }
            }
            Check(phases.size()==5 &&
                  phases.count(SupportedBodyShiftPlan::Phase::SettleX2Y5Roll025) &&
                  phases.count(SupportedBodyShiftPlan::Phase::ShiftX2Y5Roll025) &&
                  phases.count(SupportedBodyShiftPlan::Phase::HoldX2Y5Roll025) &&
                  phases.count(SupportedBodyShiftPlan::Phase::RecenterX2Y5Roll025) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Complete),
                  "roll025 mode contains only body-shift/roll phases");
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "roll025 target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "roll025 target speed limit unchanged");
            const Eigen::Matrix3d rotation=Eigen::AngleAxisd(
                SupportedBodyShiftPlan::kX2Y5Roll025Rad,
                Eigen::Vector3d::UnitX()).toRotationMatrix();
            for(int leg=0;leg<4;++leg) {
                const auto nominal=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),roll025.stand()[leg]);
                const auto shifted=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),
                    roll025.x2y5_roll025_target()[leg]);
                const Eigen::Vector3d translation(
                    SupportedBodyShiftPlan::kX2Y5Roll025ShiftXM,
                    SupportedBodyShiftPlan::kX2Y5Roll025ShiftYM,0.0);
                Check((shifted-rotation.transpose()*(nominal-translation)).norm()<5e-6,
                      "roll025 IK uses exact X/Y/roll target");
            }
            std::cout << "ROLL025_TARGET";
            for(const auto& q:roll025.x2y5_roll025_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            SupportedBodyShiftPlan support05(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                SupportedBodyShiftPlan::RunMode::LevelX2Y5Support05Only);
            SupportedBodyShiftPlan base_y5(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                SupportedBodyShiftPlan::RunMode::LevelY5Only);
            std::set<SupportedBodyShiftPlan::Phase> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(support05.total_seconds()*1000)+2;++n) {
                const auto sample=support05.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        support05.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                    Check(sample.command(joint,4)==0.0f,
                          "support05 feed-forward torque remains zero");
                }
            }
            Check(phases.size()==5 &&
                  phases.count(SupportedBodyShiftPlan::Phase::SettleX2Y5Support05) &&
                  phases.count(SupportedBodyShiftPlan::Phase::ShiftX2Y5Support05) &&
                  phases.count(SupportedBodyShiftPlan::Phase::HoldX2Y5Support05) &&
                  phases.count(SupportedBodyShiftPlan::Phase::RecenterX2Y5Support05) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Complete),
                  "support05 mode contains only body-shift/support phases");
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "support05 target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "support05 target speed limit unchanged");
            for(int leg=0;leg<4;++leg) {
                const auto nominal=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),support05.stand()[leg]);
                const auto shifted=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),
                    support05.x2y5_support05_target()[leg]);
                Eigen::Vector3d expected=nominal-Eigen::Vector3d(
                    SupportedBodyShiftPlan::kX2Y5Support05ShiftXM,
                    SupportedBodyShiftPlan::kX2Y5Support05ShiftYM,0.0);
                expected.z()-=
                    SupportedBodyShiftPlan::kX2Y5SupportExtensionM[leg];
                Check((shifted-expected).norm()<5e-6,
                      "support05 IK uses exact X/Y/support extension");
            }
            Check((support05.x2y5_support05_target()[1]-
                   base_y5.y5_target()[1]).norm()<1e-10,
                  "support05 leaves FR target exactly unchanged");
            Check((support05.x2y5_support05_target()[2]-
                   base_y5.y5_target()[2]).norm()<1e-10,
                  "support05 leaves HL target exactly unchanged");
            std::cout << "SUPPORT05_TARGET";
            for(const auto& q:support05.x2y5_support05_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            SupportedBodyShiftPlan support075(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                SupportedBodyShiftPlan::RunMode::LevelX2Y5Support075Only);
            SupportedBodyShiftPlan base_y5(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                SupportedBodyShiftPlan::RunMode::LevelY5Only);
            std::set<SupportedBodyShiftPlan::Phase> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(support075.total_seconds()*1000)+2;++n) {
                const auto sample=support075.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        support075.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                    Check(sample.command(joint,4)==0.0f,
                          "support075 feed-forward torque remains zero");
                }
            }
            Check(phases.size()==5 &&
                  phases.count(SupportedBodyShiftPlan::Phase::SettleX2Y5Support075) &&
                  phases.count(SupportedBodyShiftPlan::Phase::ShiftX2Y5Support075) &&
                  phases.count(SupportedBodyShiftPlan::Phase::HoldX2Y5Support075) &&
                  phases.count(SupportedBodyShiftPlan::Phase::RecenterX2Y5Support075) &&
                  phases.count(SupportedBodyShiftPlan::Phase::Complete),
                  "support075 mode contains only body-shift/support phases");
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "support075 target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "support075 target speed limit unchanged");
            for(int leg=0;leg<4;++leg) {
                const auto nominal=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),support075.stand()[leg]);
                const auto shifted=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),
                    support075.x2y5_support075_target()[leg]);
                Eigen::Vector3d expected=nominal-Eigen::Vector3d(
                    SupportedBodyShiftPlan::kX2Y5Support05ShiftXM,
                    SupportedBodyShiftPlan::kX2Y5Support05ShiftYM,0.0);
                expected.z()-=
                    SupportedBodyShiftPlan::kX2Y5Support075ExtensionM[leg];
                Check((shifted-expected).norm()<5e-6,
                      "support075 IK uses exact X/Y/support extension");
            }
            Check((support075.x2y5_support075_target()[1]-
                   base_y5.y5_target()[1]).norm()<1e-10,
                  "support075 leaves FR target exactly unchanged");
            Check((support075.x2y5_support075_target()[2]-
                   base_y5.y5_target()[2]).norm()<1e-10,
                  "support075 leaves HL target exactly unchanged");
            std::cout << "SUPPORT075_TARGET";
            for(const auto& q:support075.x2y5_support075_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            using R=SupportedBodyShiftPlan::RunMode;
            using P=SupportedBodyShiftPlan::Phase;
            const std::array<R,3> modes{{
                R::PhysicalCandidate1Only,R::PhysicalCandidate2Only,
                R::PhysicalCandidate3Only}};
            const std::array<std::array<P,4>,3> expected_phases{{
                {{P::SettlePhysicalCandidate1,P::ShiftPhysicalCandidate1,
                  P::HoldPhysicalCandidate1,P::RecenterPhysicalCandidate1}},
                {{P::SettlePhysicalCandidate2,P::ShiftPhysicalCandidate2,
                  P::HoldPhysicalCandidate2,P::RecenterPhysicalCandidate2}},
                {{P::SettlePhysicalCandidate3,P::ShiftPhysicalCandidate3,
                  P::HoldPhysicalCandidate3,P::RecenterPhysicalCandidate3}}}};
            const std::array<std::array<double,4>,3> extensions{{
                SupportedBodyShiftPlan::kPhysicalCandidate1ExtensionM,
                SupportedBodyShiftPlan::kPhysicalCandidate2ExtensionM,
                SupportedBodyShiftPlan::kPhysicalCandidate3ExtensionM}};
            SupportedBodyShiftPlan base_y5(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                R::LevelY5Only);
            for(int candidate=0;candidate<3;++candidate) {
                SupportedBodyShiftPlan plan(
                    SupportedBodyShiftPlan::GainStrategy::KeepStand,
                    modes[candidate]);
                std::set<P> phases;
                double max_delta=0.0,max_speed=0.0;
                for(int n=0;n<=static_cast<int>(plan.total_seconds()*1000)+2;++n) {
                    const auto sample=plan.At(n*.001);
                    phases.insert(sample.phase);
                    for(int joint=0;joint<12;++joint) {
                        max_delta=std::max(max_delta,std::abs(
                            static_cast<double>(sample.command(joint,1))-
                            plan.stand()[joint/3][joint%3]));
                        max_speed=std::max(max_speed,std::abs(
                            static_cast<double>(sample.command(joint,3))));
                        Check(sample.command(joint,4)==0.0f,
                              "physical candidate feed-forward torque zero");
                    }
                }
                Check(phases.size()==5 && phases.count(P::Complete),
                      "physical candidate has four phases plus complete");
                for(const auto phase:expected_phases[candidate])
                    Check(phases.count(phase)==1,
                          "physical candidate phase present");
                Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                      "physical candidate target delta limit unchanged");
                Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                      "physical candidate speed limit unchanged");
                for(int leg=0;leg<4;++leg) {
                    const auto nominal=lite3::FootPositionBody(
                        static_cast<lite3::Leg>(leg),plan.stand()[leg]);
                    const auto shifted=lite3::FootPositionBody(
                        static_cast<lite3::Leg>(leg),
                        plan.physical_candidate_target(candidate)[leg]);
                    Eigen::Vector3d expected=nominal-Eigen::Vector3d(
                        SupportedBodyShiftPlan::kX2Y5Support05ShiftXM,
                        SupportedBodyShiftPlan::kX2Y5Support05ShiftYM,0.0);
                    expected.z()-=extensions[candidate][leg];
                    Check((shifted-expected).norm()<5e-6,
                          "physical candidate exact support IK");
                }
                Check((plan.physical_candidate_target(candidate)[1]-
                       base_y5.y5_target()[1]).norm()<1e-10,
                      "physical candidate leaves FR unchanged");
                Check((plan.physical_candidate_target(candidate)[2]-
                       base_y5.y5_target()[2]).norm()<1e-10,
                      "physical candidate leaves HL unchanged");
                std::cout << "PHYSICAL_CANDIDATE " << candidate+1 << " TARGET";
                for(const auto& q:plan.physical_candidate_target(candidate))
                    for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
                std::cout << " MAX_DELTA " << max_delta
                          << " MAX_TARGET_SPEED " << max_speed << '\n';
            }
        }

        {
            using R=SupportedBodyShiftPlan::RunMode;
            using P=SupportedBodyShiftPlan::Phase;
            SupportedBodyShiftPlan plan(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                R::PhysicalPitchN025Only);
            std::set<P> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(plan.total_seconds()*1000)+2;++n) {
                const auto sample=plan.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        plan.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                    Check(sample.command(joint,4)==0.0f,
                          "physical pitch feed-forward torque zero");
                }
            }
            for(const auto phase:{P::SettlePhysicalPitchN025,
                    P::ShiftPhysicalPitchN025,P::HoldPhysicalPitchN025,
                    P::RecenterPhysicalPitchN025,P::Complete})
                Check(phases.count(phase)==1,"physical pitch phase present");
            Check(phases.size()==5,"physical pitch has no extra phase");
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "physical pitch target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "physical pitch speed limit unchanged");
            const Eigen::Matrix3d rotation=Eigen::AngleAxisd(
                SupportedBodyShiftPlan::kPhysicalPitchN025Rad,
                Eigen::Vector3d::UnitY()).toRotationMatrix();
            for(int leg=0;leg<4;++leg) {
                const auto nominal=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),plan.stand()[leg]);
                const auto shifted=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),
                    plan.physical_pitch_n025_target()[leg]);
                Eigen::Vector3d expected=rotation.transpose()*
                    (nominal-Eigen::Vector3d(
                        SupportedBodyShiftPlan::kX2Y5Support05ShiftXM,
                        SupportedBodyShiftPlan::kX2Y5Support05ShiftYM,0.0));
                expected.z()-=
                    SupportedBodyShiftPlan::kPhysicalCandidate1ExtensionM[leg];
                Check((shifted-expected).norm()<5e-6,
                      "physical pitch exact IK");
            }
            std::cout << "PHYSICAL_PITCH_N025_TARGET";
            for(const auto& q:plan.physical_pitch_n025_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            using R=SupportedBodyShiftPlan::RunMode;
            using P=SupportedBodyShiftPlan::Phase;
            SupportedBodyShiftPlan plan(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                R::PhysicalPitchP025Only);
            std::set<P> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(plan.total_seconds()*1000)+2;++n) {
                const auto sample=plan.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        plan.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                }
            }
            for(const auto phase:{P::SettlePhysicalPitchP025,
                    P::ShiftPhysicalPitchP025,P::HoldPhysicalPitchP025,
                    P::RecenterPhysicalPitchP025,P::Complete})
                Check(phases.count(phase)==1,"positive pitch phase present");
            Check(phases.size()==5,"positive pitch has no extra phase");
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "positive pitch target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "positive pitch speed limit unchanged");
            std::cout << "PHYSICAL_PITCH_P025_TARGET";
            for(const auto& q:plan.physical_pitch_p025_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            using R=SupportedBodyShiftPlan::RunMode;
            using P=SupportedBodyShiftPlan::Phase;
            SupportedBodyShiftPlan plan(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                R::PhysicalHeightP05Only);
            std::set<P> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(plan.total_seconds()*1000)+2;++n) {
                const auto sample=plan.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        plan.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                }
            }
            for(const auto phase:{P::SettlePhysicalHeightP05,
                    P::ShiftPhysicalHeightP05,P::HoldPhysicalHeightP05,
                    P::RecenterPhysicalHeightP05,P::Complete})
                Check(phases.count(phase)==1,"height phase present");
            Check(phases.size()==5,"height mode has no extra phase");
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "height target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "height speed limit unchanged");
            std::cout << "PHYSICAL_HEIGHT_P05_TARGET";
            for(const auto& q:plan.physical_height_p05_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            using R=SupportedBodyShiftPlan::RunMode;
            using P=SupportedBodyShiftPlan::Phase;
            SupportedBodyShiftPlan plan(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                R::PhysicalGeometryExpandOnly);
            std::set<P> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(plan.total_seconds()*1000)+2;++n) {
                const auto sample=plan.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        plan.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                }
            }
            for(const auto phase:{P::SettlePhysicalGeometryExpand,
                    P::ShiftPhysicalGeometryExpand,P::HoldPhysicalGeometryExpand,
                    P::RecenterPhysicalGeometryExpand,P::Complete})
                Check(phases.count(phase)==1,"geometry phase present");
            Check(phases.size()==5,"geometry mode has no extra phase");
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "geometry target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "geometry speed limit unchanged");
            for(int leg=0;leg<4;++leg) {
                const auto nominal=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),plan.stand()[leg]);
                const auto shifted=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),
                    plan.physical_geometry_expand_target()[leg]);
                Eigen::Vector3d expected=nominal-Eigen::Vector3d(
                    SupportedBodyShiftPlan::kX2Y5Support05ShiftXM,
                    SupportedBodyShiftPlan::kX2Y5Support05ShiftYM,0.0)+
                    Eigen::Vector3d(
                        SupportedBodyShiftPlan::kPhysicalGeometryExpandOffsetM[leg][0],
                        SupportedBodyShiftPlan::kPhysicalGeometryExpandOffsetM[leg][1],
                        0.0);
                expected.z()-=
                    SupportedBodyShiftPlan::kPhysicalCandidate1ExtensionM[leg];
                Check((shifted-expected).norm()<5e-6,"geometry exact IK");
            }
            std::cout << "PHYSICAL_GEOMETRY_EXPAND_TARGET";
            for(const auto& q:plan.physical_geometry_expand_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            using R=SupportedBodyShiftPlan::RunMode;
            using P=SupportedBodyShiftPlan::Phase;
            SupportedBodyShiftPlan plan(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                R::PhysicalForceOpt1Only);
            std::set<P> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(plan.total_seconds()*1000)+2;++n) {
                const auto sample=plan.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        plan.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                    Check(sample.command(joint,4)==0.0f,
                          "force-opt feed-forward torque remains zero");
                }
            }
            for(const auto phase:{P::SettlePhysicalForceOpt1,
                    P::ShiftPhysicalForceOpt1,P::HoldPhysicalForceOpt1,
                    P::RecenterPhysicalForceOpt1,P::Complete})
                Check(phases.count(phase)==1,"force-opt phase present");
            Check(phases.size()==5,"force-opt has no extra phase");
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "force-opt target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "force-opt speed limit unchanged");
            Check(std::abs(plan.total_seconds()-
                    (SupportedBodyShiftPlan::kSettleSeconds+
                     SupportedBodyShiftPlan::kPhysicalForceOptShiftSeconds+
                     SupportedBodyShiftPlan::kHoldSeconds+
                     SupportedBodyShiftPlan::kPhysicalForceOptRecenterSeconds))<1e-12,
                  "force-opt uses candidate-only slower ramp");
            Check(max_speed<0.0067,
                  "force-opt slower ramp has target-speed margin");
            const double recenter_peak_speed=
                1.875*max_delta/
                SupportedBodyShiftPlan::kPhysicalForceOptRecenterSeconds;
            Check(recenter_peak_speed<0.0044,
                  "force-opt recenter has additional target-speed margin");
            SupportedBodyShiftPlan base_y5(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,R::LevelY5Only);
            const std::array<Eigen::Vector3d,4> expected{{
                Eigen::Vector3d( 0.00632858,-0.75172162,1.47242728),
                Eigen::Vector3d(-0.0167054439148,-0.77216783713,1.51175805905),
                Eigen::Vector3d(-0.01707707,-0.76241208,1.50300447),
                Eigen::Vector3d(-0.02225601,-0.77474549,1.48768409)}};
            for(int leg=0;leg<4;++leg)
                Check((plan.physical_force_opt1_target()[leg]-expected[leg]).norm()
                          <1e-12,
                      "force-opt low-friction exact target");
            Check((plan.physical_force_opt1_target()[1]-
                   base_y5.y5_target()[1]).norm()<1e-7,
                  "force-opt leaves FR target unchanged");
            for(int leg=0;leg<4;++leg) {
                const auto foot=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),
                    plan.physical_force_opt1_target()[leg]);
                const auto solved=lite3::SolveFootIk(
                    static_cast<lite3::Leg>(leg),foot,plan.stand()[leg]);
                Check(solved.converged && solved.residual_m<5e-6,
                      "force-opt target passes full IK");
            }
            std::cout << "PHYSICAL_FORCE_OPT1_TARGET";
            for(const auto& q:plan.physical_force_opt1_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            using R=SupportedBodyShiftPlan::RunMode;
            using P=SupportedBodyShiftPlan::Phase;
            SupportedBodyShiftPlan plan(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                R::PhysicalBalancedOnly);
            const std::array<Eigen::Vector3d,4> expected{{
                Eigen::Vector3d( 0.00719844,-0.75150758,1.47061913),
                Eigen::Vector3d(-0.0167054439148,-0.77216783713,1.51175805905),
                Eigen::Vector3d(-0.01697933,-0.76077520,1.50439662),
                Eigen::Vector3d(-0.02199410,-0.77565856,1.48483468)}};
            std::set<P> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(plan.total_seconds()*1000)+2;++n) {
                const auto sample=plan.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        plan.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                    Check(sample.command(joint,4)==0.0f,
                          "balanced feed-forward torque remains zero");
                }
            }
            for(const auto phase:{P::SettlePhysicalBalanced,
                    P::ShiftPhysicalBalanced,P::HoldPhysicalBalanced,
                    P::RecenterPhysicalBalanced,P::Complete})
                Check(phases.count(phase)==1,"balanced phase present");
            Check(phases.size()==5,"balanced has no lift/extra phase");
            for(int leg=0;leg<4;++leg)
                Check((plan.physical_balanced_target()[leg]-expected[leg]).norm()
                          <1e-12,"balanced exact target");
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "balanced target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "balanced target speed limit unchanged");
            std::cout << "PHYSICAL_BALANCED_TARGET";
            for(const auto& q:plan.physical_balanced_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            using R=SupportedBodyShiftPlan::RunMode;
            using P=SupportedBodyShiftPlan::Phase;
            SupportedBodyShiftPlan plan(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                R::PhysicalForceOpt2Only);
            const std::array<Eigen::Vector3d,4> expected{{
                Eigen::Vector3d( 0.02400000,-0.74897953,1.48877879),
                Eigen::Vector3d( 0.00455403,-0.74902766,1.49676761),
                Eigen::Vector3d( 0.02043046,-0.74973161,1.51624438),
                Eigen::Vector3d(-0.01323031,-0.74897953,1.47650035)}};
            std::set<P> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(plan.total_seconds()*1000)+2;++n) {
                const auto sample=plan.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        plan.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                    Check(sample.command(joint,4)==0.0f,
                          "force-opt2 feed-forward torque remains zero");
                }
            }
            for(const auto phase:{P::SettlePhysicalForceOpt2,
                    P::ShiftPhysicalForceOpt2,P::HoldPhysicalForceOpt2,
                    P::RecenterPhysicalForceOpt2,P::Complete})
                Check(phases.count(phase)==1,"force-opt2 phase present");
            Check(phases.size()==5,"force-opt2 has no lift/extra phase");
            for(int leg=0;leg<4;++leg) {
                Check((plan.physical_force_opt2_target()[leg]-expected[leg]).norm()
                          <1e-12,"force-opt2 exact target");
                const auto foot=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),
                    plan.physical_force_opt2_target()[leg]);
                const auto solved=lite3::SolveFootIk(
                    static_cast<lite3::Leg>(leg),foot,plan.stand()[leg]);
                Check(solved.converged && solved.residual_m<5e-6,
                      "force-opt2 exact target passes full IK");
            }
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "force-opt2 target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "force-opt2 target speed limit unchanged");
            Check(std::abs(plan.total_seconds()-
                    (SupportedBodyShiftPlan::kSettleSeconds+
                     SupportedBodyShiftPlan::kPhysicalForceOpt2ShiftSeconds+
                     SupportedBodyShiftPlan::kHoldSeconds+
                     SupportedBodyShiftPlan::kPhysicalForceOpt2RecenterSeconds))<1e-12,
                  "force-opt2 uses conservative outbound/recenter timing");
            Check(max_speed<0.0038,
                  "force-opt2 outbound target-speed margin");
            std::cout << "PHYSICAL_FORCE_OPT2_TARGET";
            for(const auto& q:plan.physical_force_opt2_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            using R=SupportedBodyShiftPlan::RunMode;
            using P=SupportedBodyShiftPlan::Phase;
            SupportedBodyShiftPlan plan(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                R::PhysicalForceOpt3Only);
            const std::array<Eigen::Vector3d,4> expected{{
                Eigen::Vector3d(-0.024299096505,-0.759888805242,1.473223518359),
                Eigen::Vector3d(-0.024422283795,-0.773094561530,1.498466216521),
                Eigen::Vector3d(-0.024550385820,-0.774774886517,1.501744331328),
                Eigen::Vector3d(-0.024492295561,-0.779558889389,1.510881397003)}};
            std::set<P> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(plan.total_seconds()*1000)+2;++n) {
                const auto sample=plan.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        plan.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                    Check(sample.command(joint,4)==0.0f,
                          "force-opt3 feed-forward torque remains zero");
                }
            }
            for(const auto phase:{P::SettlePhysicalForceOpt3,
                    P::ShiftPhysicalForceOpt3,P::HoldPhysicalForceOpt3,
                    P::RecenterPhysicalForceOpt3,P::Complete})
                Check(phases.count(phase)==1,"force-opt3 phase present");
            Check(phases.size()==5,"force-opt3 has no lift/extra phase");
            for(int leg=0;leg<4;++leg) {
                Check((plan.physical_force_opt3_target()[leg]-expected[leg]).norm()
                          <1e-12,"force-opt3 exact frozen target");
                const auto foot=lite3::FootPositionBody(
                    static_cast<lite3::Leg>(leg),expected[leg]);
                const auto solved=lite3::SolveFootIk(
                    static_cast<lite3::Leg>(leg),foot,plan.stand()[leg]);
                Check(solved.converged && solved.residual_m<5e-6,
                      "force-opt3 target passes full IK");
            }
            Check(max_delta<=SupportedBodyShiftPlan::kMaxJointDeltaRad+1e-7,
                  "force-opt3 target delta limit unchanged");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "force-opt3 target speed limit unchanged");
            Check(max_speed<0.0043,
                  "force-opt3 conservative target-speed margin");
            std::cout << "PHYSICAL_FORCE_OPT3_TARGET";
            for(const auto& q:plan.physical_force_opt3_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            using R=SupportedBodyShiftPlan::RunMode;
            using P=SupportedBodyShiftPlan::Phase;
            SupportedBodyShiftPlan plan(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                R::PhysicalLargeLeanOnly);
            const std::array<Eigen::Vector3d,4> expected{{
                Eigen::Vector3d(-0.115346035671,-0.651753680867,1.386078585201),
                Eigen::Vector3d(-0.116505019629,-0.698275921138,1.480210774755),
                Eigen::Vector3d(-0.119065894876,-0.698685080701,1.482467953121),
                Eigen::Vector3d(-0.119517220868,-0.737292999462,1.560953685317)}};
            std::set<P> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(plan.total_seconds()*1000)+2;++n) {
                const auto sample=plan.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        plan.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                    Check(sample.command(joint,4)==0.0f,
                          "large-lean feed-forward torque remains zero");
                }
            }
            for(const auto phase:{P::SettlePhysicalLargeLean,
                    P::ShiftPhysicalLargeLean,P::HoldPhysicalLargeLean,
                    P::RecenterPhysicalLargeLean,P::Complete})
                Check(phases.count(phase)==1,"large-lean phase present");
            Check(phases.size()==5,"large-lean has no lift/extra phase");
            for(int leg=0;leg<4;++leg) {
                Check((plan.physical_large_lean_target()[leg]-expected[leg]).norm()
                          <1e-12,"large-lean exact frozen target");
                for(int joint=0;joint<3;++joint) {
                    Check(expected[leg][joint]>=lite3::LowerLimits()[joint] &&
                          expected[leg][joint]<=lite3::UpperLimits()[joint],
                          "large-lean target within vendor joint limits");
                }
            }
            Check(max_delta<=plan.max_joint_delta_rad()+1e-7,
                  "large-lean stays inside its reviewed one-use envelope");
            Check(max_delta>SupportedBodyShiftPlan::kMaxJointDeltaRad,
                  "large-lean does not silently reuse old research envelope");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "large-lean target speed limit unchanged");
            std::cout << "PHYSICAL_LARGE_LEAN_TARGET";
            for(const auto& q:plan.physical_large_lean_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed << '\n';
        }

        {
            using R=SupportedBodyShiftPlan::RunMode;
            using P=SupportedBodyShiftPlan::Phase;
            SupportedBodyShiftPlan plan(
                SupportedBodyShiftPlan::GainStrategy::KeepStand,
                R::PhysicalStagedSupportTriangleOnly);
            const std::array<Eigen::Vector3d,4> expected{{
                Eigen::Vector3d(-0.046272076671,-0.658245015638,1.456162689392),
                Eigen::Vector3d( 0.0,-0.725124435087,1.498135726020),
                Eigen::Vector3d(-0.046272076671,-0.754742539017,1.465600853330),
                Eigen::Vector3d( 0.057710789225,-0.726625500337,1.455523736311)}};
            std::set<P> phases;
            double max_delta=0.0,max_speed=0.0;
            for(int n=0;n<=static_cast<int>(plan.total_seconds()*1000)+2;++n) {
                const auto sample=plan.At(n*.001);
                phases.insert(sample.phase);
                for(int joint=0;joint<12;++joint) {
                    max_delta=std::max(max_delta,std::abs(
                        static_cast<double>(sample.command(joint,1))-
                        plan.stand()[joint/3][joint%3]));
                    max_speed=std::max(max_speed,std::abs(
                        static_cast<double>(sample.command(joint,3))));
                    Check(sample.command(joint,4)==0.0f,
                          "staged stance feed-forward torque remains zero");
                }
            }
            Check(std::abs(plan.total_seconds()-94.0)<1e-12,
                  "staged stance has bounded total duration");
            Check(phases.size()==36,"staged stance has exact reviewed phases");
            for(const auto phase:{P::StagedSettle,P::StagedFLUnload,
                    P::StagedFLLift,P::StagedFLMove,P::StagedFLLower,
                    P::StagedHLUnload,P::StagedHLLift,P::StagedHLMove,
                    P::StagedHLLower,P::StagedHRUnload,P::StagedHRLift,
                    P::StagedHRMove,P::StagedHRLower,P::StagedFinalShift,
                    P::StagedFinalHold,P::StagedBodyRecenter,
                    P::StagedRestoreHRLift,P::StagedRestoreHLLift,
                    P::StagedRestoreFLLift,P::StagedFinalStand,P::Complete})
                Check(phases.count(phase)==1,"staged stance phase present");
            std::cout << "STAGED_SUPPORT_TARGET";
            for(const auto& q:plan.staged_final_target())
                for(int joint=0;joint<3;++joint) std::cout << ' ' << q[joint];
            std::cout << " MAX_DELTA " << max_delta
                      << " MAX_TARGET_SPEED " << max_speed
                      << " TOTAL_SECONDS " << plan.total_seconds() << '\n';
            for(int leg=0;leg<4;++leg)
                Check((plan.staged_final_target()[leg]-expected[leg]).norm()<1e-8,
                      "staged stance exact final target");
            Check(max_delta<=plan.max_joint_delta_rad()+1e-7,
                  "staged stance inside one-use joint envelope");
            Check(max_speed<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS+1e-7,
                  "staged stance target speed limit unchanged");
            Check(max_speed<0.07,"staged stance retains target-speed margin");
        }

        SupportedBodyShiftPlan smooth(
            SupportedBodyShiftPlan::GainStrategy::SmoothReduced);
        Check(smooth.At(0).command(0,0)==SupportedBodyShiftPlan::kStandKp,
              "smooth starts at stand kp");
        Check(std::abs(smooth.At(
            SupportedBodyShiftPlan::kGainRampSeconds).command(0,0)-
            SupportedBodyShiftPlan::kReducedKp)<1e-5,
            "smooth reaches reduced kp");

        std::cout << "supported body-shift calibration plan: PASS\n";
        return 0;
    } catch(const std::exception& e) {
        std::cerr << "supported body-shift plan: FAIL: " << e.what() << '\n';
        return 1;
    }
}
