// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

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
//   standard security policy. The acting identity must also have host.shell
//   authorization; the environment flag alone does not grant it.
//   During regression capture, child stdout and stderr are merged into routed
//   output so LOG records them and QUIET suppresses their screen presentation.
//   Captured commands report their child exit status; -1 means capture failed.
//   An interactive shell (bare BANG or !) is refused during regression capture.
//   Outside regression capture, the ordinary host-shell behavior is unchanged.
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
//   REGRESSION
//

#include "xbase.hpp"
#include "textio.hpp"
#include "cli/command_output.hpp"
#include "help/helpdata_messages.hpp"
#include "cli/external_process_policy.hpp"
#include "identity/identity_admin.hpp"

#include <iostream>
#include <string>
#include <cstdlib>
#include "cli/captured_process.hpp"
#include "cli/output_router.hpp"
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
    std::cout << "\n  - Host-command policy and acting-identity host.shell authorization apply.\n"
                 "  - During regression capture, child stdout/stderr follow LOG and QUIET.\n"
                 "    Interactive shells are refused; captured child exit status is reported.\n";
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

    // Identity enforcement (AIF-045 2c-5b): the acting member must be authorized for
    // host.shell. The owner is exempt; a non-owner agent needs a live grant. This is
    // additive to the DOTTALK_ALLOW_HOST_COMMANDS gate below, so owner behavior is
    // unchanged (still off-by-default). For host.* the identity check also folds in
    // the host-command policy, so a granted agent still needs host commands enabled.
    {
        const dottalk::identity::Decision d = dottalk::identity::agent_permitted("host.shell");
        if (!d.allowed()) {
            std::cout << "BANG: refused for " << dottalk::identity::acting_member_key()
                      << " -- " << d.reason << "\n";
            return;
        }
    }

    if (!cli::security::authorize_external_process("BANG", false))
        return;

    // A regression capture must include child stdout/stderr too. Keep the
    // ordinary interactive shell path unchanged outside a captured run.
    if (cli::OutputRouter::instance().capture_active()) {
        if (rest.empty()) {
            std::cout << "BANG: interactive shells are unavailable during regression capture.\n";
            return;
        }
        const int code = cli::stream_shell_output(rest, cli::OutputRouter::instance().out());
        std::cout << "BANG: captured child exit status " << code << "\n";
        return;
    }

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
