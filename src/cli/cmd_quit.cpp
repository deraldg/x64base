// src/cli/cmd_quit.cpp
// @dottalk.usage v1
// owner: DOT|QUIT
// command: QUIT
// aliases: EXIT
// category: shell
// status: supported
// noargs: execute
// effect: session-control
// mutates: shell-exit-state
// usage-access: QUIT USAGE
// summary:
//   Request DotTalk++ shell shutdown without mutating open table data,
//   HELP data, metadata catalogs, manualgen artifacts, or source files.
//
// usage:
//   QUIT
//   EXIT
//
// notes:
//   QUIT and EXIT share the same implementation.
//   Extra arguments print usage and do not request shell shutdown.
//   QUIT sets only the shell-exit request flag; cleanup remains owned by the
//   surrounding shell/session lifecycle.
//
// risk:
//   exits_shell: yes
//   writes_dbf_record: no
//   writes_table_buffer: no
//   writes_files: no
//   launches_external_app: no
//   network_access: no
//
// related:
//   HELP
//   ABOUT
//
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
