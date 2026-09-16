#pragma once
#include <atomic>
#include <chrono>
#include <memory>
class StateMachine;
// Unforgeable by console/controllers: only StateMachine creates/renews a bounded grant.
// This is operator authorization, NEVER evidence of MotionSDK ownership.
class StandOnlyPermit {
    friend class StateMachine;
    std::shared_ptr<const std::atomic<bool>> abort_;
    const std::atomic<bool>* signal_;
    using Clock=std::chrono::steady_clock;
    mutable std::atomic<Clock::duration::rep> expires_;
    static constexpr std::chrono::seconds lifetime{8};
    StandOnlyPermit(std::shared_ptr<const std::atomic<bool>> abort,
                    const std::atomic<bool>* signal,
                    std::chrono::steady_clock::time_point expires)
        : abort_(std::move(abort)), signal_(signal), expires_(expires.time_since_epoch().count()) {}
    // StateMachine may call ONLY after a fresh TARGET_REACHED monitor result.
    // Never resurrect an expired/cancelled permit or confer SDK ownership.
    bool RenewSupportedHold() const {
        const auto now=Clock::now();
        if(Cancelled() || now.time_since_epoch().count()>=expires_.load()) return false;
        expires_.store((now+lifetime).time_since_epoch().count());
        return !Cancelled();
    }
public:
    double RemainingSeconds() const {
        return std::chrono::duration<double>(Clock::duration(expires_.load())-Clock::now().time_since_epoch()).count();
    }
    bool Cancelled() const { return abort_->load() || (signal_ && signal_->load()); }
    bool Valid() const {
        return !abort_->load() && (!signal_ || !signal_->load()) &&
            Clock::now().time_since_epoch().count()<expires_.load();
    }
};
