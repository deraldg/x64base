// cmd_pshell_help.cpp

// @dottalk.usage v1
// owner: DOT|PSHELL
// command: PSHELL
// category: reference
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: PSHELL USAGE
// summary:
//   Display the PowerShell/PSHELL helper reference and search the curated
//   PowerShell one-liner catalog.
//
// usage:
//   PSHELL
//   PSHELL USAGE
//   PSHELL LIST-CATEGORIES
//   PSHELL <category>
//   PSHELL <term>
//
// examples:
//   PSHELL
//   PSHELL PYTHON
//   PSHELL PY-VENV-CREATE
//   PSHELL CLEAN
//
// notes:
//   PSHELL with no arguments displays the grouped PSHELL reference.
//   PSHELL USAGE prints command usage without searching the catalog.
//   PSHELL is read-only and does not execute PowerShell commands.
//
// risk:
//   mutates_table_data: no
//   executes_shell: no
//
// related:
//   HELP
//   SQLHELP
//   PS
//

#include "xbase.hpp"
#include <sstream>
#include <string>
#include <algorithm>
#include <cctype>
#include <iostream>
#include "cli/command_output.hpp"

static std::string pshell_usage_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool pshell_usage_request(const std::string& raw)
{
    const std::string u = pshell_usage_upper(raw);
    return u == "USAGE" || u == "HELP" || u == "?";
}

static void print_pshell_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::PshellUsageText);
}
// Forward declaration from cmd_pshell.cpp
extern void show_pshell_help(const std::string& arg);

void cmd_PSHELL(xbase::DbArea& /*area*/, std::istringstream& iss) {
    std::string args;
    std::getline(iss >> std::ws, args);   // everything after "PSHELL"
    if (pshell_usage_request(args)) {
        print_pshell_usage();
        return;
    }
    show_pshell_help(args);
}

void cmd_PS(xbase::DbArea& area, std::istringstream& iss) {
    cmd_PSHELL(area, iss);   // alias
}
