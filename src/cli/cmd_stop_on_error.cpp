// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_stop_on_error.cpp
// STOP_ON_ERROR [severity] -- set or report the DotScript stop-on-error threshold.

// @dottalk.usage v1
// owner: DOT|STOP_ON_ERROR
// command: STOP_ON_ERROR
// category: diagnostics
// status: supported
// noargs: report
// effect: session-state
// mutates: errorstop-policy
// usage-access: STOP_ON_ERROR USAGE
// summary:
//   Set or report the severity threshold at which a running DotScript aborts.
//
// usage:
//   STOP_ON_ERROR
//   STOP_ON_ERROR OFF | WARNING | ERROR
//   STOP_ON_ERROR USAGE
//
// notes:
//   STOP_ON_ERROR with no arguments reports the current threshold.
//   OFF (default) never aborts; WARNING aborts on warning-or-worse; ERROR aborts
//   on error only. Accepts OFF|NONE|0, WARNING|WARN|1, ERROR|FATAL|2.
//   The startup default is read from the DOTTALK_ERRORSTOP environment variable.
//   SET ERRORSTOP TO <severity> is the compatibility form of this command.
//   The threshold is compared against the severity carried by the canonical
//   error code recorded through the message/emit_error path (errors derive from
//   messaging), so only real recorded errors can trip it.
//
// risk:
//   reads_error_state: yes
//   mutates_output_format_state: no
//   mutates_table_data: no
//
// related:
//   ERROR_STATUS
//   SET ERRORSTOP
//

#include <algorithm>
#include <cctype>
#include <sstream>
#include <string>

#include "cli/command_output.hpp"
#include "xbase.hpp"
#include "xbase_error_codes.hpp"
#include "xbase_error_context.hpp"

namespace {

std::string trim_copy(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back())))  s.pop_back();
    return s;
}

std::string upper_copy(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

} // namespace

// CLI command: STOP_ON_ERROR
void cmd_STOP_ON_ERROR(xbase::DbArea& A, std::istringstream& in)
{
    (void)A;

    // Take the argument portion, drop an inline "&&" comment, keep the first token.
    std::string tail;
    std::getline(in, tail);
    const std::string::size_type amp = tail.find("&&");
    if (amp != std::string::npos) tail.erase(amp);
    std::string arg;
    {
        std::istringstream toks(tail);
        toks >> arg;
    }
    arg = trim_copy(arg);

    // No argument -> report current threshold.
    if (arg.empty()) {
        cli::cmdout::print_info(
            "STOP_ON_ERROR",
            std::string("threshold is ") +
                xbase::error::errorstop_level_name(xbase::error::get_errorstop()));
        return;
    }

    const std::string u = upper_copy(arg);
    if (u == "USAGE" || u == "HELP" || u == "?") {
        cli::cmdout::print_info("STOP_ON_ERROR",
            "STOP_ON_ERROR [OFF|WARNING|ERROR] | USAGE  "
            "(OFF never aborts; WARNING aborts on warning-or-worse; ERROR aborts on error).");
        return;
    }

    bool ok = false;
    const xbase::error::errorstop_level lvl = xbase::error::parse_errorstop_level(u, &ok);
    if (!ok) {
        // Invalid severity is itself a recorded error (flows through the error
        // state so it is observable by ERROR_STATUS and stop-on-error).
        xbase::error::set_last_error(xbase::error::e_invalid_argument());
        cli::cmdout::print_info(
            "STOP_ON_ERROR",
            std::string("invalid severity '") + arg + "'; use OFF, WARNING, or ERROR.");
        return;
    }

    xbase::error::set_errorstop(lvl);
    cli::cmdout::print_info(
        "STOP_ON_ERROR",
        std::string("threshold set to ") + xbase::error::errorstop_level_name(lvl));
}
