#include "cli/shell_exit_request.hpp"

#include <atomic>

namespace {

std::atomic_bool g_shell_exit_requested{false};

} // namespace

namespace xbase {

void request_shell_exit() {
    g_shell_exit_requested.store(true, std::memory_order_release);
}

void clear_shell_exit_request() {
    g_shell_exit_requested.store(false, std::memory_order_release);
}

bool shell_exit_requested() {
    return g_shell_exit_requested.load(std::memory_order_acquire);
}

} // namespace xbase