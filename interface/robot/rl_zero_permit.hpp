#pragma once
#include <atomic>
#include <chrono>
#include <memory>
class StateMachine;
class HardwareInterface;
// Separate, non-renewable operator grant. NOT SDK ownership confirmation.
class RLZeroPermit {
    friend class StateMachine;
    friend class HardwareInterface;
    using Clock=std::chrono::steady_clock;
    std::shared_ptr<const std::atomic<bool>> abort_;
    const std::atomic<bool>* signal_;
    const Clock::time_point expires_;
    mutable std::atomic<Clock::duration::rep> last_send_;
    RLZeroPermit(std::shared_ptr<const std::atomic<bool>> abort, const std::atomic<bool>* signal)
        : abort_(std::move(abort)), signal_(signal), expires_(Clock::now()+std::chrono::seconds(8)),
          last_send_(Clock::now().time_since_epoch().count()) {}
    void Sent() const {last_send_.store(Clock::now().time_since_epoch().count());}
public:
    const char* FailureReason() const {
        const auto now=Clock::now();
        if(abort_->load() || (signal_ && signal_->load())) return "RL zero permit cancelled";
        if(now>=expires_) return "RL zero 8s deadline";
        if(now-Clock::time_point(Clock::duration(last_send_.load()))>=std::chrono::milliseconds(300))
            return "RL zero policy-send timeout 300ms";
        return nullptr;
    }
    bool Valid() const {return FailureReason()==nullptr;}
    double RemainingSeconds() const {return std::chrono::duration<double>(expires_-Clock::now()).count();}
};
