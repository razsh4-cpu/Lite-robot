#pragma once
// OFFLINE SPECIFICATION ONLY. Not included/linked by any production target.
// This models limited operator authorization, NEVER ownership confirmation.
#include <cstdint>
namespace stand_review {
enum class Phase { Locked, Armed, Pending, Active, Revoked };
enum class Controller { Idle, Stand, RL, Damping };
struct Conditions {
    std::uint64_t acquisition_session{0};
    bool acquisition_requested{false};
    bool feedback_fresh{false};
    bool passive_health_reviewed{false};
    bool estop_ready{false};
    bool operator_present{false};
    bool normalized_velocity_zero{false};
    bool joint_gate_closed{false};
    Controller controller{Controller::Idle};
};
class Authorization {
    Phase phase_{Phase::Locked};
    std::uint64_t session_{0};
    std::int64_t deadline_ms_{0};
    static constexpr std::int64_t arm_window_ms=5000;
    static constexpr std::int64_t active_window_ms=10000;
    bool ContextValid(std::int64_t now, const Conditions& c) const {
        return now>=0 && now<deadline_ms_ &&
            c.acquisition_session==session_ && c.acquisition_requested &&
            c.feedback_fresh && c.passive_health_reviewed && c.estop_ready &&
            c.operator_present && c.normalized_velocity_zero;
    }
public:
    Phase phase() const { return phase_; }
    const char* ownership() const { return "OWNERSHIP_UNCONFIRMED"; }
    bool authorize_once(std::int64_t now, const Conditions& c) {
        // A duplicate arm must neither extend nor replace a live grant.
        if(phase_!=Phase::Locked || now<0 || c.acquisition_session==0 ||
           (session_!=0 && c.acquisition_session!=session_) ||
           c.controller!=Controller::Idle || !c.joint_gate_closed ||
           !c.acquisition_requested || !c.feedback_fresh ||
           !c.passive_health_reviewed || !c.estop_ready ||
           !c.operator_present || !c.normalized_velocity_zero) return false;
        session_=c.acquisition_session;
        deadline_ms_=now+arm_window_ms;
        phase_=Phase::Armed;
        return true;
    }
    bool request_stand(std::int64_t now, const Conditions& c) {
        if(phase_!=Phase::Armed) return false;
        if(!ContextValid(now,c) || c.controller!=Controller::Idle || !c.joint_gate_closed) {
            revoke(); return false;
        }
        phase_=Phase::Pending; // STILL NO SEND PERMISSION
        return true;
    }
    bool entered_stand(std::int64_t now, const Conditions& c) {
        if(phase_!=Phase::Pending) return false;
        if(!ContextValid(now,c) || c.controller!=Controller::Stand || !c.joint_gate_closed) {
            revoke(); return false;
        }
        phase_=Phase::Active;
        deadline_ms_=now+active_window_ms;
        return true;
    }
    bool permit_stand_output(std::int64_t now, const Conditions& c,
                             Controller producer, bool finite_joint_output) {
        if(phase_!=Phase::Active) return false;
        if(!ContextValid(now,c) || c.controller!=Controller::Stand ||
           producer!=Controller::Stand || !finite_joint_output) {
            revoke(); return false;
        }
        return true;
    }
    bool request_rl() const { return false; }
    bool permit_nonzero_velocity() const { return false; }
    void revoke() { phase_=Phase::Revoked; }
    bool begin_new_acquisition_session(std::uint64_t session) {
        // Caller must have completed the old release and a fresh explicit
        // acquisition. Never reuse old session IDs or turn this into confirmation.
        if(phase_!=Phase::Revoked || session==0 || session<=session_) return false;
        phase_=Phase::Locked; session_=session; deadline_ms_=0; return true;
    }
};
} // namespace stand_review
