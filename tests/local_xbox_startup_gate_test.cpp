#include "local_xbox_startup_gate.hpp"

#include <cassert>
#include <iostream>
#include <string>
#include <unistd.h>

int main() {
    const std::string path="/tmp/lite3-xbox-startup-gate-"+
        std::to_string(static_cast<long long>(getpid()))+".lock";
    unlink(path.c_str());

    bool hardware_constructed=false;
    CommandSourceLease invalid_device_lease(path);
    LocalXboxStartupGate invalid_device(invalid_device_lease);
    if(invalid_device.Prepare(false)) hardware_constructed=true;
    assert(!hardware_constructed);
    assert(!invalid_device_lease.Held());

    CommandSourceLease autonomy(path);
    assert(autonomy.TryAcquire(CommandSource::Autonomy));
    CommandSourceLease blocked_local_lease(path);
    LocalXboxStartupGate blocked_local(blocked_local_lease);
    if(blocked_local.Prepare(true)) hardware_constructed=true;
    assert(!hardware_constructed);
    assert(!blocked_local_lease.Held());

    autonomy.Release();
    CommandSourceLease selected_local_lease(path);
    LocalXboxStartupGate selected_local(selected_local_lease);
    if(selected_local.Prepare(true) && selected_local.HardwareConstructionAllowed())
        hardware_constructed=true;
    assert(hardware_constructed);
    assert(selected_local_lease.Source()==CommandSource::LocalXbox);
    selected_local_lease.Release();
    unlink(path.c_str());
    std::cout<<"local_xbox_startup_gate_test PASS\n";
}
