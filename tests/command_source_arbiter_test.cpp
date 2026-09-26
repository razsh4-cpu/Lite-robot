#include "command_source_arbiter.hpp"

#include <cassert>
#include <fstream>
#include <iostream>
#include <string>
#include <unistd.h>

int main() {
    const std::string path="/tmp/lite3-command-source-"+
        std::to_string(static_cast<long long>(getpid()))+".lock";
    unlink(path.c_str());

    CommandSourceLease autonomy(path),local(path),laptop(path);
    assert(autonomy.TryAcquire(CommandSource::Autonomy));
    assert(!local.TryAcquire(CommandSource::LocalXbox));
    assert(!laptop.TryAcquire(CommandSource::LaptopXbox));
    autonomy.Release();
    assert(local.TryAcquire(CommandSource::LocalXbox));
    local.Release();
    assert(laptop.TryAcquire(CommandSource::LaptopXbox));
    laptop.Release();

    std::ifstream in(path);
    std::string state;
    std::getline(in,state);
    assert(state=="COMMAND_SOURCE=NONE");
    unlink(path.c_str());
    std::cout<<"command_source_arbiter_test PASS\n";
}
