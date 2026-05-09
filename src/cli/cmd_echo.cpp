// src/cli/cmd_echo.cpp
// @dottalk.usage v1
// owner: DOT|ECHO
// command: ECHO
// category: output
// status: supported
// noargs: report
// effect: output
// mutates: output-stream
// usage-access: ECHO USAGE
// summary:
//   Print or comment-echo text through the output router depending on SET ECHO state.
//
// usage:
//   ECHO
//   ECHO USAGE
//   ECHO <text>
//
// notes:
//   ECHO with no arguments preserves existing behavior and emits an empty comment/output line.
//   ECHO <text> is comment-style console output when router echo is OFF.
//   ECHO <text> routes normally when router echo is ON.
//   ECHO ON is not the toggle command; use SET ECHO ON or SET ECHO OFF.
//   ECHO USAGE prints usage directly and does not route through echo mode.
//
// risk:
//   writes_output: yes
//   mutates_table_data: no
//   changes_echo_mode: no
//
// related:
//   SET ECHO
//   PRINT
//   ALTERNATE
//

#include "xbase.hpp"
#include <sstream>
#include <iostream>
#include <string>
#include <algorithm>
#include <cctype>

#include "cli/output_router.hpp"

namespace {
static std::string echo_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string echo_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool is_echo_usage_request(const std::string& raw)
{
    std::string t = echo_upper(echo_trim(raw));
    if (t.rfind("ECHO ", 0) == 0) {
        t = echo_upper(echo_trim(t.substr(5)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_echo_usage()
{
    std::cout
        << "Usage:\n"
        << "  ECHO\n"
        << "  ECHO USAGE\n"
        << "  ECHO <text>\n"
        << "Notes:\n"
        << "  - ECHO ON is not the toggle command; use SET ECHO ON or SET ECHO OFF.\n";
}
} // namespace


// ECHO behavior requirement:
// - Default: SET ECHO OFF (router default)
// - When ECHO is OFF: ECHO <string> is ignored by the system and becomes
//   a comment string to console.
// - When ECHO is ON: output is routed normally (console/print/alternate apply).
//
// Important:
// - "ECHO ON" is NOT the toggle command.
// - Use "SET ECHO ON|OFF" to change router echo mode.

void cmd_ECHO(xbase::DbArea&, std::istringstream& iss)
{
    std::string rest;
    std::getline(iss, rest);
    if (!rest.empty() && rest.front() == ' ')
        rest.erase(0, 1);

    if (is_echo_usage_request(rest)) {
        print_echo_usage();
        return;
    }

    auto& R = cli::OutputRouter::instance();

    if (!R.echo_on()) {
        // Comment-style console output, forced directly to console.
        // This intentionally bypasses router switches so comments remain visible
        // even if SET CONSOLE OFF or alternate/print routing changes.
        if (!rest.empty()) std::cout << "; " << rest << "\n";
        else               std::cout << ";\n";
        return;
    }

    // Echo ON: route normally through the current output paths.
    R.out() << rest << "\n";
}