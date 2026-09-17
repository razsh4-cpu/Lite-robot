#pragma once
#include "robot_interface.h"
#include "motion_sdk_transport.hpp"
#include <chrono>
#include <cmath>
#include <functional>
#include <limits>
#include <mutex>
#include <stdexcept>
#include "stand_diagnostics.hpp"
#include <vector>
#include <algorithm>
#include <fstream>
#include <iomanip>
#include <unistd.h>

class HardwareInterface : public interface::RobotInterface {
public:
    using Clock = std::chrono::steady_clock;
    using Now = std::function<Clock::time_point()>;
private:
    struct FeedbackStore {
        std::mutex mutex;
        RobotData data{};
        RobotData invalid_data{}; // diagnostic only; never extends freshness
        bool seen{false};
        bool invalid{false};
        Clock::time_point last_progress{};
    };
    std::shared_ptr<FeedbackStore> feedback_ = std::make_shared<FeedbackStore>();
    std::shared_ptr<MotionSdkTransport> transport_;
    mutable std::mutex send_mutex_;
    bool started_{false}, request_sent_{false}, joint_enabled_{false};
    bool supported_leg_test_bounds_{false};
    std::shared_ptr<const StandOnlyPermit> stand_permit_;
    std::shared_ptr<const RLZeroPermit> rl_zero_permit_;
    std::shared_ptr<const RLForwardPermit> rl_forward_permit_;
    std::chrono::milliseconds telemetry_timeout_;
    Now now_;
    std::vector<stand_diagnostics::Record> stand_records_;
    stand_diagnostics::Record last_record_{};
    double stand_elapsed_=0;
    stand_diagnostics::MonitorStatus monitor_diagnostics_;
    size_t diagnostic_dropped_=0;
    size_t diagnostic_head_=0;
    bool rl_zero_diagnostics_=false;
    bool rl_forward_diagnostics_=false;
    double rl_zero_entry_wall_=0;
    uint64_t policy_started_=0, policy_completed_=0;
    std::array<double,3> normalized_{{NAN,NAN,NAN}};
    bool policy_snapshot_valid_=false;
    std::array<double,45> policy_observation_{};
    std::array<double,12> policy_raw_action_{};
    bool diagnostics_active_=false;
    std::array<double,12> entry_metadata_q_{}, entry_metadata_dq_{};
    double entry_metadata_stamp_=0;
    static constexpr size_t diagnostic_capacity_=24000;
    void Remember(stand_diagnostics::Record r) {
        r.monitor=monitor_diagnostics_;
        r.rl_zero=rl_zero_diagnostics_;
        r.rl_forward=rl_forward_diagnostics_;
        if(r.rl_zero || r.rl_forward) {
            r.elapsed=r.wall-rl_zero_entry_wall_;
            r.policy_started=policy_started_;r.policy_completed=policy_completed_;
            r.normalized=normalized_;
            r.policy_snapshot_valid=policy_snapshot_valid_;
            r.policy_observation=policy_observation_;
            r.policy_raw_action=policy_raw_action_;
        }
        last_record_=r;
        if(stand_records_.size()<diagnostic_capacity_) stand_records_.push_back(r);
        else {
            // Bounded tail ring: long stand holds must not discard later RL/abort evidence.
            stand_records_[diagnostic_head_]=r;
            diagnostic_head_=(diagnostic_head_+1)%diagnostic_capacity_;
            ++diagnostic_dropped_;
        }
    }

    RobotData Snapshot() const {
        std::lock_guard<std::mutex> lock(feedback_->mutex);
        return feedback_->data;
    }
    static bool Valid(const RobotData& d) {
        for (float v : d.imu.buffer_float) if (!std::isfinite(v)) return false;
        for (const auto& j : d.joint_data.joint_data)
            if (!std::isfinite(j.position) || !std::isfinite(j.velocity) ||
                !std::isfinite(j.torque)) return false;
        return true;
    }
public:
    explicit HardwareInterface(const std::string& name,
        std::string ip = "192.168.1.120", int port = 43893);
    HardwareInterface(const std::string& name, std::shared_ptr<MotionSdkTransport> transport,
        std::chrono::milliseconds timeout = std::chrono::milliseconds(300),
        Now now = [] { return Clock::now(); })
        : RobotInterface(name, 12), transport_(std::move(transport)),
          telemetry_timeout_(timeout), now_(std::move(now)) {
        if (!transport_ || timeout.count() <= 0) throw std::invalid_argument("hardware safety configuration");
        joint_cmd_ = MatXf::Zero(12, 5);
        stand_records_.reserve(diagnostic_capacity_);
    }
    void Start() override {
        std::lock_guard<std::mutex> lock(send_mutex_);
        if (started_) return;
        std::weak_ptr<FeedbackStore> weak = feedback_;
        const auto now = now_;
        transport_->StartFeedback([weak, now](const RobotData& data) {
            const auto store = weak.lock();
            if (!store) return;
            std::lock_guard<std::mutex> lock(store->mutex);
            if(!Valid(data)) { store->invalid=true; store->invalid_data=data; return; }
            const auto delta = static_cast<uint32_t>(data.tick - store->data.tick);
            // Frozen/backward ticks don't extend freshness; uint32 wrap works.
            if (!store->seen || (delta > 0 && delta < 0x80000000u)) {
                store->data = data;
                store->last_progress = now();
                store->seen = true;
                store->invalid = false;
            }
        });
        started_ = true;
    }
    double FeedbackAgeSeconds() const override {
        std::lock_guard<std::mutex> lock(feedback_->mutex);
        if (!feedback_->seen || feedback_->invalid) return std::numeric_limits<double>::infinity();
        return std::chrono::duration<double>(now_() - feedback_->last_progress).count();
    }
    bool IsFeedbackFresh() const override {
        const auto age=FeedbackAgeSeconds();
        return age>=0 && age <= std::chrono::duration<double>(telemetry_timeout_).count();
    }
    StandFeedback GetStandFeedback() override {
        std::lock_guard<std::mutex> lock(feedback_->mutex);
        const auto& d=feedback_->invalid ? feedback_->invalid_data : feedback_->data;
        StandFeedback s; s.q.resize(12); s.dq.resize(12); s.torque.resize(12);
        for(int i=0;i<12;++i) {
            s.q[i]=d.joint_data.joint_data[i].position;
            s.dq[i]=d.joint_data.joint_data[i].velocity;
            s.torque[i]=d.joint_data.joint_data[i].torque;
        }
        s.rpy=Vec3f(d.imu.angle_roll,d.imu.angle_pitch,d.imu.angle_yaw)*M_PI/180.;
        s.stamp=d.tick*.001;
        s.age=feedback_->seen ? std::chrono::duration<double>(now_()-feedback_->last_progress).count()
                              : std::numeric_limits<double>::infinity();
        s.fresh=feedback_->seen && !feedback_->invalid && s.age>=0 &&
            s.age<=std::chrono::duration<double>(telemetry_timeout_).count();
        s.valid=!feedback_->invalid;
        return s;
    }
    void SetStandDiagnosticContext(double elapsed) override {
        std::lock_guard<std::mutex> lock(send_mutex_); stand_elapsed_=elapsed;
    }
    void SetStandMonitorDiagnostics(const stand_diagnostics::MonitorStatus& status) override {
        std::lock_guard<std::mutex> lock(send_mutex_); monitor_diagnostics_=status;
    }
    void RecordStandEntryMetadata(const VecXf& q, const VecXf& dq, double stamp) override {
        std::lock_guard<std::mutex> lock(send_mutex_);
        if(q.size()!=12 || dq.size()!=12) return;
        for(int i=0;i<12;++i) {entry_metadata_q_[i]=q[i];entry_metadata_dq_[i]=dq[i];}
        entry_metadata_stamp_=stamp;
    }
    std::string LastStandSendReason() const override {
        std::lock_guard<std::mutex> lock(send_mutex_);
        return stand_diagnostics::Name(last_record_.reason);
    }
    stand_diagnostics::Record LastStandRecord() const {
        std::lock_guard<std::mutex> lock(send_mutex_); return last_record_;
    }
    void RecordPolicyProgress(const Vec3f& cmd, bool completed) override {
        std::lock_guard<std::mutex> lock(send_mutex_);
        if(!rl_zero_diagnostics_ && !rl_forward_diagnostics_) return;
        for(int i=0;i<3;++i) normalized_[i]=cmd[i];
        if(completed) ++policy_completed_; else ++policy_started_;
    }
    void RecordPolicySnapshot(const std::array<double,45>& observation,
                              const std::array<double,12>& raw_action) override {
        std::lock_guard<std::mutex> lock(send_mutex_);
        if(!rl_zero_diagnostics_ && !rl_forward_diagnostics_) return;
        policy_observation_=observation;
        policy_raw_action_=raw_action;
        policy_snapshot_valid_=true;
    }
    void RecordStandEvent(int event, const std::string& cause) override {
        std::lock_guard<std::mutex> lock(send_mutex_);
        if(!diagnostics_active_) return;
        using R=stand_diagnostics::Reason;
        stand_diagnostics::Record r;
        r.event=event; r.reason=R::STATE_CHANGED;
        r.event_detail=cause;
        r.target_valid=event!=1;
        if(cause=="tracking error") r.reason=R::TRACKING_ERROR;
        else if(cause=="stale telemetry") r.reason=R::STALE_FEEDBACK;
        else if(cause=="tilt limit") r.reason=R::EXCESSIVE_TILT;
        else if(cause=="invalid IMU" || cause=="invalid measured joints" || cause=="invalid measured feedback") r.reason=R::INVALID_MEASURED_STATE;
        else if(cause=="invalid target") r.reason=R::INVALID_COMMAND;
        r.wall=std::chrono::duration<double>(Clock::now().time_since_epoch()).count();
        r.elapsed=stand_elapsed_; r.gate=joint_enabled_; r.requested=request_sent_;
        r.permit_valid=stand_permit_&&stand_permit_->Valid();
        r.permit_remaining=stand_permit_?stand_permit_->RemainingSeconds():0;
        if(rl_zero_permit_) {r.permit_valid=rl_zero_permit_->Valid();r.permit_remaining=rl_zero_permit_->RemainingSeconds();}
        if(rl_forward_permit_) {r.permit_valid=rl_forward_permit_->Valid();r.permit_remaining=rl_forward_permit_->RemainingSeconds();}
        if(rl_zero_permit_) {
            r.permit_valid=rl_zero_permit_->Valid();r.permit_remaining=rl_zero_permit_->RemainingSeconds();
        }
        auto s=GetStandFeedback(); r.feedback_age=s.age; r.tick=s.stamp; r.roll=s.rpy[0]; r.pitch=s.rpy[1];
        for(int i=0;i<12;++i) {
            r.position[i]=s.q[i]; r.velocity[i]=s.dq[i]; r.torque[i]=s.torque[i];
            r.target[i]=joint_cmd_(i,1); r.target_velocity[i]=joint_cmd_(i,3);
            double e=std::abs(r.target[i]-r.position[i]);
            if(e>r.max_error){r.max_error=e;r.joint=i;}
        }
        Remember(r);
    }
    // Deferred disk I/O: called only AFTER the shared abort has closed the gate
    // and attempted ownership return. No console/file writes in the send loop.
    void FinishStandDiagnostics(const std::string& ending) override {
        std::vector<stand_diagnostics::Record> records;
        std::array<double,12> entry_q,entry_dq; double entry_stamp;
        size_t dropped;
        {
            std::lock_guard<std::mutex> lock(send_mutex_);
            if(!diagnostics_active_) return;
            diagnostics_active_=false; records=stand_records_; dropped=diagnostic_dropped_;
            std::rotate(records.begin(),records.begin()+diagnostic_head_,records.end());
            entry_q=entry_metadata_q_; entry_dq=entry_metadata_dq_; entry_stamp=entry_metadata_stamp_;
        }
        const std::string path="/tmp/lite3-stand-trace-"+std::to_string(getpid())+"-"+
            std::to_string(std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now().time_since_epoch()).count())+".jsonl";
        std::ofstream out(path); out<<std::setprecision(12);
        auto number=[&](double x){ if(std::isfinite(x)) out<<x; else out<<"null"; };
        out<<"{\"metadata_only\":true,\"entry_tick_s\":";number(entry_stamp);
        out<<",\"entry_q\":[";
        for(int i=0;i<12;++i) {if(i)out<<',';number(entry_q[i]);}
        out<<"],\"entry_dq\":[";
        for(int i=0;i<12;++i) {if(i)out<<',';number(entry_dq[i]);} out<<"]}\n";
        for(const auto& r:records) {
            out<<"{\"event\":"<<r.event<<",\"reason\":\""<<stand_diagnostics::Name(r.reason)<<"\",\"phase\":\""
               <<(r.rl_forward?"RL_FORWARD":r.rl_zero?"RL_ZERO":r.elapsed<=1.5?"PREPARATION":r.elapsed<3?"RAISING":"FINAL_HOLD")<<"\",\"wall_s\":"; number(r.wall);
            out<<",\"policy_started\":"<<r.policy_started<<",\"policy_completed\":"<<r.policy_completed;
            out<<",\"normalized_command\":[";
            for(int i=0;i<3;++i){if(i)out<<',';number(r.normalized[i]);}out<<']';
            out<<",\"elapsed_s\":"; number(r.elapsed); out<<",\"feedback_age_s\":"; number(r.feedback_age);
            out<<",\"feedback_tick_s\":"; number(r.tick); out<<",\"permit_remaining_s\":"; number(r.permit_remaining);
            out<<",\"roll\":"; number(r.roll); out<<",\"pitch\":"; number(r.pitch);
            out<<",\"max_error\":"; number(r.max_error);
            out<<",\"monitor_wall_s\":"; number(r.monitor.wall);
            out<<",\"monitor_elapsed_s\":"; number(r.monitor.elapsed);
            out<<",\"convergence_timer_s\":"; number(r.monitor.dwell_elapsed);
            out<<",\"observation_timer_s\":"; number(r.monitor.observation_elapsed);
            out<<",\"raw_max_speed\":"; number(r.monitor.raw_max_speed);
            out<<",\"rms_max_speed_50ms\":"; number(r.monitor.rms_max_speed);
            out<<",\"position_range_speed_50ms\":"; number(r.monitor.position_range_speed);
            out<<",\"speed_window_ready\":"<<r.monitor.speed_window_ready;
            out<<",\"convergence_candidate\":"<<r.monitor.candidate
               <<",\"final_target\":"<<r.monitor.final_target
               <<",\"monitor_new_feedback\":"<<r.monitor.new_feedback
               <<",\"monitor_reason\":\""<<r.monitor.reason<<"\""
               <<",\"event_detail\":\""<<r.event_detail<<"\"";
            out<<",\"joint\":"<<r.joint<<",\"leg\":\""<<stand_diagnostics::Leg(r.joint)
               <<"\",\"joint_name\":\""<<stand_diagnostics::Joint(r.joint)<<"\",\"tracking_limit\":0.35,\"tilt_limit\":0.35"
               <<",\"gate\":"<<r.gate<<",\"request_sent\":"<<r.requested<<",\"ownership\":\""
               <<(r.requested?"OWNERSHIP_UNCONFIRMED":"NOT_REQUESTED")<<"\",\"permit_valid\":"<<r.permit_valid<<",\"sent\":"<<r.sent
               <<",\"target_valid\":"<<r.target_valid;
            auto array=[&](const char* name,const std::array<double,12>& values) {
                out<<",\""<<name<<"\":["; for(int i=0;i<12;++i) {if(i) out<<','; number(values[i]);} out<<']';
            };
            array("target",r.target); array("target_velocity",r.target_velocity);
            array("position",r.position); array("velocity",r.velocity); array("torque",r.torque);
            out<<",\"policy_snapshot_valid\":"<<r.policy_snapshot_valid;
            out<<",\"policy_observation\":[";
            for(int i=0;i<45;++i){if(i)out<<',';number(r.policy_observation[i]);}out<<']';
            out<<",\"policy_raw_action\":[";
            for(int i=0;i<12;++i){if(i)out<<',';number(r.policy_raw_action[i]);}out<<']';
            std::array<double,12> error; for(int i=0;i<12;++i) error[i]=r.target[i]-r.position[i];
            array("error",error); out<<"}\n";
        }
        // Ending strings are internal constants; no operator-controlled text.
        out<<"{\"end_reason\":\""<<ending<<"\",\"records\":"<<records.size()<<",\"dropped\":"<<dropped<<"}\n";
        out.flush();
        std::cerr<<"STAND_TRACE "<<(out?path:"WRITE_FAILED")<<" records="<<records.size()<<" dropped="<<dropped<<std::endl;
    }
    bool AcquireControl() override {
        std::lock_guard<std::mutex> lock(send_mutex_);
        if (!started_ || !IsFeedbackFresh()) return false;
        if (request_sent_) return true;
        joint_enabled_ = false;
        supported_leg_test_bounds_ = false;
        stand_permit_.reset();
        transport_->RequestOwnership(2);
        request_sent_ = true;
        return true;
    }
    void ReleaseControl() override {
        std::lock_guard<std::mutex> lock(send_mutex_);
        joint_enabled_ = false;
        supported_leg_test_bounds_ = false;
        rl_zero_permit_.reset();
        rl_forward_permit_.reset();
        stand_permit_.reset();
        supported_leg_test_bounds_ = false;
        if (!request_sent_) return;
        transport_->RequestOwnership(1); // excludes all in-flight SendJoints
        request_sent_ = false;
    }
    // RobotData/SDK provide no authoritative ownership acknowledgment.
    bool IsControlAcquired() const override { return false; }
    bool IsControlRequestSent() const override {
        std::lock_guard<std::mutex> lock(send_mutex_); return request_sent_;
    }
    const char* OwnershipStatus() const override {
        return IsControlRequestSent() ? "OWNERSHIP_UNCONFIRMED" : "NOT_REQUESTED";
    }
    void SetJointCommandEnabled(bool enabled) override {
        std::lock_guard<std::mutex> lock(send_mutex_);
        rl_zero_permit_.reset();
        rl_forward_permit_.reset();
        stand_permit_.reset();
        // Generic gate still requires confirmation; supervised stand uses a private grant.
        // No production confirmation source: acquisition-only is allowed,
        // but actuator streaming remains blocked pending a reviewed mechanism.
        joint_enabled_ = enabled && request_sent_ && IsControlAcquired() && IsFeedbackFresh();
    }
    bool JointCommandsEnabled() const override {
        std::lock_guard<std::mutex> lock(send_mutex_); return joint_enabled_;
    }
    void Stop() override { ReleaseControl(); }
    double GetInterfaceTimeStamp() override { return Snapshot().tick * 0.001; }
    VecXf GetJointPosition() override {
        auto d=Snapshot(); VecXf v(12);
        for(int i=0;i<12;++i) v(i)=d.joint_data.joint_data[i].position;
        return v;
    }
    VecXf GetJointVelocity() override {
        auto d=Snapshot(); VecXf v(12);
        for(int i=0;i<12;++i) v(i)=d.joint_data.joint_data[i].velocity;
        return v;
    }
    VecXf GetJointTorque() override {
        auto d=Snapshot(); VecXf v(12);
        for(int i=0;i<12;++i) v(i)=d.joint_data.joint_data[i].torque;
        return v;
    }
    Vec3f GetImuRpy() override {
        auto d=Snapshot(); return Vec3f(d.imu.angle_roll,d.imu.angle_pitch,d.imu.angle_yaw)/180.*M_PI;
    }
    Vec3f GetImuAcc() override {
        auto d=Snapshot(); return Vec3f(d.imu.acc_x,d.imu.acc_y,d.imu.acc_z);
    }
    Vec3f GetImuOmega() override {
        auto d=Snapshot(); return Vec3f(d.imu.angular_velocity_roll,d.imu.angular_velocity_pitch,d.imu.angular_velocity_yaw);
    }
    VecXf GetContactForce() override {
        const auto d=Snapshot();
        VecXf force_z(4);
        force_z << d.contact_force.fl_leg[2], d.contact_force.fr_leg[2],
                   d.contact_force.hl_leg[2], d.contact_force.hr_leg[2];
        return force_z;
    }
    MatXf GetJointCommand() override {
        std::lock_guard<std::mutex> lock(send_mutex_); return joint_cmd_;
    }
    void SetJointCommand(Eigen::Matrix<float, Eigen::Dynamic, 5> input) override {
        std::lock_guard<std::mutex> lock(send_mutex_);
        using R=stand_diagnostics::Reason;
        stand_diagnostics::Record r;
        r.wall=std::chrono::duration<double>(Clock::now().time_since_epoch()).count();
        r.elapsed=stand_elapsed_; r.gate=joint_enabled_; r.requested=request_sent_;
        r.target_valid=input.rows()==12 && input.allFinite();
        r.permit_valid=stand_permit_ && stand_permit_->Valid();
        r.permit_remaining=stand_permit_?stand_permit_->RemainingSeconds():0;
        if(rl_zero_permit_) {
            r.permit_valid=rl_zero_permit_->Valid();
            r.permit_remaining=rl_zero_permit_->RemainingSeconds();
        }
        if(rl_forward_permit_) {
            r.permit_valid=rl_forward_permit_->Valid();
            r.permit_remaining=rl_forward_permit_->RemainingSeconds();
        }
        const auto s=GetStandFeedback();
        r.feedback_age=s.age; r.tick=s.stamp; r.roll=s.rpy[0]; r.pitch=s.rpy[1];
        for(int i=0;i<12;++i) {
            r.position[i]=s.q[i]; r.velocity[i]=s.dq[i]; r.torque[i]=s.torque[i];
            r.target[i]=input.rows()==12?input(i,1):std::numeric_limits<double>::quiet_NaN();
            r.target_velocity[i]=input.rows()==12?input(i,3):std::numeric_limits<double>::quiet_NaN();
            const double e=std::abs(r.target[i]-r.position[i]);
            if(e>r.max_error) {r.max_error=e; r.joint=i;}
        }
        auto reject=[&](R reason) {r.reason=reason; joint_enabled_=false; Remember(r);};
        if(!request_sent_ || !joint_enabled_) {
            // Expected idle writes are not retained; attempted sends still expose a reason.
            r.reason=R::SEND_GATE_CLOSED; last_record_=r;
            if(diagnostics_active_) Remember(r);
            return;
        }
        if(stand_permit_ && !r.permit_valid) {
            reject(stand_permit_->Cancelled()?R::STATE_CHANGED:R::PERMIT_EXPIRED); return;
        }
        if(rl_zero_permit_ && !r.permit_valid) {reject(R::PERMIT_EXPIRED); return;}
        if(rl_forward_permit_ && !r.permit_valid) {reject(R::PERMIT_EXPIRED); return;}
        if(!s.valid || !s.q.allFinite() || !s.dq.allFinite() || !s.rpy.allFinite()) {
            for(int i=0;i<12;++i) if(!std::isfinite(s.q[i]) || !std::isfinite(s.dq[i]) || !std::isfinite(s.torque[i])) {r.joint=i;break;}
            reject(R::INVALID_MEASURED_STATE); return;
        }
        if(!s.fresh) {reject(R::STALE_FEEDBACK); return;}
        if(input.rows()!=12 || !input.allFinite()) {
            if(input.rows()==12) for(int i=0;i<12;++i) if(!input.row(i).allFinite()) {r.joint=i;break;}
            reject(R::INVALID_COMMAND); return;
        }
        if(stand_permit_ || rl_zero_permit_ || rl_forward_permit_) {
            if(std::abs(r.roll)>0.35 || std::abs(r.pitch)>0.35) {reject(R::EXCESSIVE_TILT); return;}
            for(int i=0;i<12;++i) if(input(i,0)<0 || input(i,2)<0 || input(i,4)!=0) {
                r.joint=i; reject(R::INVALID_COMMAND); return;
            }
            if(r.max_error>0.35) {reject(R::TRACKING_ERROR); return;}
        }
        if(supported_leg_test_bounds_) {
            constexpr double stand[3]={0.0,-0.7729795255029084,1.5005003509817765};
            if(!stand_permit_ || std::abs(r.roll)>3.0*M_PI/180.0 ||
               std::abs(r.pitch)>3.0*M_PI/180.0 || s.dq.cwiseAbs().maxCoeff()>0.50) {
                reject(R::EXCESSIVE_TILT); return;
            }
            for(int i=0;i<12;++i) {
                if(input(i,0)>60.0001 || input(i,2)>0.7001 ||
                   std::abs(input(i,1)-stand[i%3])>0.0300001 ||
                   std::abs(input(i,3))>0.1000001 ||
                   std::abs(input(i,1)-s.q[i])>0.15) {
                    r.joint=i; reject(R::INVALID_COMMAND); return;
                }
            }
        }
        RobotCmd cmd{};
        for(int i=0;i<12;++i) {
            cmd.joint_cmd[i].kp=input(i,0); cmd.joint_cmd[i].position=input(i,1);
            cmd.joint_cmd[i].kd=input(i,2); cmd.joint_cmd[i].velocity=input(i,3);
            cmd.joint_cmd[i].torque=input(i,4);
        }
        try { transport_->SendJoints(cmd); }
        catch(...) {reject(R::OTHER); throw;}
        if(rl_zero_permit_) rl_zero_permit_->Sent();
        if(rl_forward_permit_) rl_forward_permit_->Sent();
        joint_cmd_=input;
        r.reason=R::SENT; r.sent=true; Remember(r);
    }
protected:
    bool EnableSupportedLegTestBounds(bool enabled) override {
        std::lock_guard<std::mutex> lock(send_mutex_);
        if(enabled && (!joint_enabled_ || !request_sent_ || !stand_permit_ ||
                       !stand_permit_->Valid() || !IsFeedbackFresh())) return false;
        supported_leg_test_bounds_=enabled;
        return true;
    }
    bool OpenSupervisedRLZero(const std::shared_ptr<const RLZeroPermit>& permit) override {
        std::lock_guard<std::mutex> lock(send_mutex_);
        if(!permit || !permit->Valid() || !request_sent_ || joint_enabled_ || !IsFeedbackFresh()) return false;
        stand_permit_.reset(); rl_zero_permit_=permit; joint_enabled_=true;
        rl_zero_diagnostics_=true;
        rl_forward_diagnostics_=false;
        rl_zero_entry_wall_=std::chrono::duration<double>(Clock::now().time_since_epoch()).count();
        policy_started_=policy_completed_=0; normalized_={{NAN,NAN,NAN}}; policy_snapshot_valid_=false;
        return true;
    }
    bool OpenSupervisedRLForward(const std::shared_ptr<const RLForwardPermit>& permit) override {
        std::lock_guard<std::mutex> lock(send_mutex_);
        if(!permit || !permit->Valid() || !request_sent_ || joint_enabled_ || !IsFeedbackFresh())return false;
        stand_permit_.reset();rl_zero_permit_.reset();rl_forward_permit_=permit;joint_enabled_=true;
        rl_zero_diagnostics_=false;rl_forward_diagnostics_=true;
        rl_zero_entry_wall_=std::chrono::duration<double>(Clock::now().time_since_epoch()).count();
        policy_started_=policy_completed_=0;normalized_={{NAN,NAN,NAN}};policy_snapshot_valid_=false;
        return true;
    }
    bool OpenSupervisedStand(const std::shared_ptr<const StandOnlyPermit>& permit) override {
        std::lock_guard<std::mutex> lock(send_mutex_);
        if(!permit || !permit->Valid() || !request_sent_ || joint_enabled_ || !IsFeedbackFresh()) return false;
        stand_records_.clear(); diagnostic_dropped_=diagnostic_head_=0; diagnostics_active_=true; stand_elapsed_=0;
        rl_zero_diagnostics_=rl_forward_diagnostics_=false;
        monitor_diagnostics_={};
        stand_permit_=permit; joint_enabled_=true;
        supported_leg_test_bounds_=false;
        return true;
    }
};
