// @dottalk.usage v1
// owner: DOT|BANG
// command: BANG
// category: shell
// status: supported
// noargs: execute
// effect: execute
// mutates: external-process delegates-command-effects
// usage-access: BANG USAGE
// summary:
//   Launch the host operating-system shell or execute a host shell command.
//
// usage:
//   BANG
//   BANG USAGE
//   BANG <command>
//   !
//   ! <command>
//
// notes:
//   BANG with no arguments opens an interactive host shell only when host
//   commands are explicitly enabled.
//   BANG <command> executes the host command and returns only when host
//   commands are explicitly enabled.
//   The exclamation mark is a shell shortcut/alias for BANG.
//   BANG USAGE prints usage and does not launch a shell.
//   BANG may indirectly read, write, delete, or execute anything the host shell command does.
//   Set DOTTALK_ALLOW_HOST_COMMANDS=1 to enable this command under the
//   standard security policy.
//
// risk:
//   launches_external_process: yes
//   executes_host_command: yes
//   mutates_table_data: no direct mutation
//   mutates_filesystem: depends on command
//
// related:
//   PSHELL
//   SFTP
//   WEB
//

#include "xbase.hpp"
#include "textio.hpp"
#include "cli/command_output.hpp"
#include "help/helpdata_messages.hpp"
#include "cli/external_process_policy.hpp"

#include <string>
#include <cstdlib>
#include <cctype>
#include <algorithm>
#include <iostream>
#include <sstream>

namespace {
static std::string bang_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool is_bang_usage_request(std::string raw)
{
    std::string t = bang_upper(textio::trim(std::move(raw)));
    if (t.rfind("BANG ", 0) == 0) {
        t = bang_upper(textio::trim(t.substr(5)));
    } else if (t.rfind("! ", 0) == 0) {
        t = bang_upper(textio::trim(t.substr(2)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_bang_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::BangUsageText);
}
} // namespace


void cmd_BANG(xbase::DbArea&, std::istringstream& iss) {
    std::string rest;
    std::getline(iss, rest);
    rest = textio::trim(rest);

    if (is_bang_usage_request(rest)) {
        print_bang_usage();
        return;
    }

    if (!cli::security::authorize_external_process("BANG", false))
        return;

#ifdef _WIN32
    if (rest.empty()) {
        // Interactive shell
        std::system("cmd.exe");
    } else {
        // Run and return
        std::string cmd = "cmd.exe /C " + rest;
        std::system(cmd.c_str());
    }
#else
    if (rest.empty()) {
        std::system("/bin/sh");
    } else {
        std::string cmd = "/bin/sh -c \"" + rest + "\"";
        std::system(cmd.c_str());
    }
#endif
}
