
#include "state_machine.hpp"
#include <csignal>
#ifdef BUILD_SIMULATION
    #define BACKWARD_HAS_DW 1
    #include "backward.hpp"
    namespace backward{
        backward::SignalHandling sh;
    }
#endif
using namespace types;

MotionStateFeedback StateBase::msfb_ = MotionStateFeedback();

namespace {
volatile std::sig_atomic_t shutdown_requested = 0;

void RequestShutdown(int) {
    shutdown_requested = 1;
}
}  // namespace

int main(){
    std::signal(SIGINT, RequestShutdown);
    std::signal(SIGTERM, RequestShutdown);
    StateMachine state_machine(RobotType::Lite3);
    state_machine.Run(&shutdown_requested);
    return 0;
}
