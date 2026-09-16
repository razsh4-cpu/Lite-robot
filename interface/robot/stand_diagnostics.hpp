#pragma once
#include <array>
#include <string>
#include <limits>
#include <cmath>
#include <cstdint>
namespace stand_diagnostics {
// Read-only exported snapshot of monitor evidence/decisions. Logging consumers
// cannot authorize control or modify the monitor's internal evidence.
struct MonitorStatus {
    double wall=0, elapsed=0, dwell_elapsed=0, observation_elapsed=0, raw_max_speed=0;
    double rms_max_speed=0, position_range_speed=0;
    bool speed_window_ready=false;
    bool candidate=false, final_target=false, new_feedback=false;
    const char* reason="not checked";
};
enum class Reason { SENT, STALE_FEEDBACK, INVALID_COMMAND, TRACKING_ERROR,
    EXCESSIVE_TILT, PERMIT_EXPIRED, SEND_GATE_CLOSED, INVALID_MEASURED_STATE,
    STATE_CHANGED, OTHER };
inline const char* Name(Reason r) {
    switch(r) {
#define CASE(x) case Reason::x: return #x
        CASE(SENT); CASE(STALE_FEEDBACK); CASE(INVALID_COMMAND); CASE(TRACKING_ERROR);
        CASE(EXCESSIVE_TILT); CASE(PERMIT_EXPIRED); CASE(SEND_GATE_CLOSED);
        CASE(INVALID_MEASURED_STATE); CASE(STATE_CHANGED); CASE(OTHER);
#undef CASE
    } return "OTHER";
}
inline const char* Leg(int i) { static const char* a[]={"FL","FR","HL","HR"}; return i>=0&&i<12?a[i/3]:"none"; }
inline const char* Joint(int i) { static const char* a[]={"HipX","HipY","Knee"}; return i>=0&&i<12?a[i%3]:"none"; }
struct Record {
    bool rl_zero=false, rl_forward=false;
    uint64_t policy_started=0, policy_completed=0;
    std::array<double,3> normalized{{NAN,NAN,NAN}};
    double wall=0, elapsed=0, feedback_age=0, permit_remaining=0, tick=0;
    double roll=0, pitch=0, max_error=0;
    int joint=-1;
    bool permit_valid=false, gate=false, requested=false, sent=false;
    bool target_valid=false;
    int event=0; // 0=command decision, 1=stand entry, 2=supervisor abort/exit
    Reason reason=Reason::OTHER;
    MonitorStatus monitor;
    std::string event_detail;
    std::array<double,12> target{}, target_velocity{}, position{}, velocity{}, torque{};
    bool policy_snapshot_valid=false;
    std::array<double,45> policy_observation{};
    std::array<double,12> policy_raw_action{};
};
}
