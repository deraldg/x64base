// @dottalk.file v1
// subsystem: cli
// layer: command
// owns:
// project: project.x64base.runtime
// lane:
// owner: member.derald
// status: supported

// src/cli/cmd_pwd.cpp
// @dottalk.usage v1
// owner: DOT|PWD
// command: PWD
// category: diagnostics
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: PWD USAGE
// summary:
//   Print the process working directory and the DATA and DBF path slots, so a
//   user can see where relative names and bare table names will resolve.
//
// usage:
//   PWD
//   PWD USAGE
//
// notes:
//   Added 2026-11-27 after the first public beta: a new user's first command
//   was PWD and it did not exist, and `! pwd` is refused by default because
//   host shell commands are off unless explicitly enabled.
//   Read-only. It does not change directory; use SETPATH to move a slot.
//   DBF follows lane scripts: after DO X64 it names the x64 lane.
//
// risk:
//   mutates_table_data: no
//   changes_directory: no
//
// related:
//   SETPATH
//   DIR
//

#include <cctype>
#include <filesystem>
#include <sstream>
#include <string>
#include <system_error>

#include "cli/command_output.hpp"
#include "common/path_state.hpp"
#include "xbase.hpp"

namespace {
std::string pwd_upper_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

void print_pwd_usage()
{
    cli::cmdout::print_line("Usage:");
    cli::cmdout::print_line("  PWD           print the working directory and the DATA and DBF slots");
    cli::cmdout::print_line("  PWD USAGE     this text");
    cli::cmdout::print_line("Notes:");
    cli::cmdout::print_line("  - Read-only. SETPATH changes a slot; SETPATH with no arguments lists them all.");
}
} // namespace

// Shell entry point: PWD
void cmd_PWD(xbase::DbArea& /*area*/, std::istringstream& is)
{
    std::string rest;
    std::getline(is, rest);
    const std::string arg = pwd_upper_trim(rest);
    if (arg == "USAGE" || arg == "HELP" || arg == "?") {
        print_pwd_usage();
        return;
    }
    if (!arg.empty()) {
        cli::cmdout::print_line("PWD: takes no arguments (see PWD USAGE).");
        return;
    }

    std::error_code ec;
    const std::filesystem::path cwd = std::filesystem::current_path(ec);
    namespace paths = dottalk::paths;
    cli::cmdout::print_line("Working dir : " + (ec ? std::string("(unavailable)") : cwd.string()));
    cli::cmdout::print_line("DATA        : " + paths::get_slot(paths::Slot::DATA).string());
    cli::cmdout::print_line("DBF         : " + paths::get_slot(paths::Slot::DBF).string());
}
