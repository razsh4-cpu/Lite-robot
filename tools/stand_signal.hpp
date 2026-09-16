#pragma once
#include <atomic>
// Shared by the real console and inert signal tests. Handler does no I/O/locking.
namespace stand_signal {
inline std::atomic<bool> requested{false};
static_assert(std::atomic<bool>::is_always_lock_free, "signal latch must be lock-free");
inline void RequestShutdown(int) { requested.store(true); }
}
