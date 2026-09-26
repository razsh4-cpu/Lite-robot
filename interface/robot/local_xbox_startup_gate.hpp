#pragma once

#include "command_source_arbiter.hpp"

// Last in-process guard before any HardwareInterface may be constructed.
// systemd conditions are advisory; this lease closes the check/start race.
class LocalXboxStartupGate final {
public:
    explicit LocalXboxStartupGate(CommandSourceLease& lease):lease_(lease) {}

    bool Prepare(bool expected_xbox_device_valid) {
        device_valid_=expected_xbox_device_valid;
        if(!device_valid_) return false;
        lease_valid_=lease_.TryAcquire(CommandSource::LocalXbox);
        return HardwareConstructionAllowed();
    }

    bool HardwareConstructionAllowed() const {
        return device_valid_ && lease_valid_ && lease_.Held() &&
            lease_.Source()==CommandSource::LocalXbox;
    }

private:
    CommandSourceLease& lease_;
    bool device_valid_{false};
    bool lease_valid_{false};
};
