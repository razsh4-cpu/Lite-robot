#pragma once

#include <atomic>
#include <memory>

class LocalXboxStateMachine;

class LocalXboxControlPermit final {
    friend class LocalXboxStateMachine;
    std::shared_ptr<const std::atomic<bool>> cancelled_;
    explicit LocalXboxControlPermit(std::shared_ptr<const std::atomic<bool>> cancelled)
        : cancelled_(std::move(cancelled)) {}
public:
    bool Valid() const { return cancelled_ && !cancelled_->load(); }
};
