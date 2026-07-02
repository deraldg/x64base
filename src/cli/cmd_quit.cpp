#include "cli/cmd_quit.hpp"

#include <atomic>
#include <sstream>
#include <string>

#include "cli/command_output.hpp"
#include "help/helpdata_messages.hpp"

namespace {

std::atomic_bool g_shell_exit_requested{false};

bool has_extra_tokens(std::istringstream& args) {
    std::string extra;
    return static_cast<bool>(args >> extra);
}

void print_quit_usage() {
    cli::cmdout::print_message(dottalk::helpdata::MessageId::QuitUsageText);
}

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

void cmd_QUIT(xbase::DbArea&, std::istringstream& args) {
    if (has_extra_tokens(args)) {
        print_quit_usage();
        return;
    }

    xbase::request_shell_exit();
}

void cmd_EXIT(xbase::DbArea& area, std::istringstream& args) {
    cmd_QUIT(area, args);
}
