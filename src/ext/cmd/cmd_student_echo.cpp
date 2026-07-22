// @dottalk.usage v1
// owner: EXT|STUDENTECHO
// command: STUDENTECHO
// aliases: SECHO
// category: extension-example
// status: sample-extension
// noargs: usage
// effect: report
// mutates: none
// usage-access: STUDENTECHO USAGE; SECHO USAGE
// summary:
//   Student/custom extension sample that echoes the rest of the command line.
//
// usage:
//   STUDENTECHO USAGE
//   STUDENTECHO <text>
//   SECHO USAGE
//   SECHO <text>
//
// examples:
//   STUDENTECHO hello
//   SECHO hello
//
// notes:
//   Usage/help/? prints usage before echo output.
//   This is a self-registering extension example, not a protected built-in.
//
// risk:
//   mutates_table_data: no
//

#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "set_relations.hpp"
#include "cli/command_registry.hpp"
#include "../ext_policy.hpp"
#include <cctype>

/*
    Custom Command Policy
    ---------------------

    This file is a second student/custom extension example.

    - Built-in CLI commands remain protected and centrally registered.
    - Custom commands may self-register from src/ext/cmd/.
    - Use clearly custom names.
    - Avoid collisions with built-in commands.

    This sample adds:
        STUDENTECHO
        SECHO
*/

namespace {

static std::string studentecho_upper_contract(std::string s)
{
    for (char& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

static void print_studentecho_usage_contract()
{
    std::cout
        << "Usage:\n"
        << "  STUDENTECHO USAGE\n"
        << "  STUDENTECHO <text>\n"
        << "  SECHO USAGE\n"
        << "  SECHO <text>\n"
        << "Examples:\n"
        << "  STUDENTECHO hello\n"
        << "  SECHO hello\n"
        << "Notes:\n"
        << "  - USAGE/HELP/? does not echo text.\n";
}
void cmd_STUDENTECHO(xbase::DbArea&, std::istringstream& in)
{
    std::string rest;
    std::getline(in, rest);

    if (!rest.empty() && rest.front() == ' ') {
        rest.erase(rest.begin());
    }

    // STUDENTECHO_USAGE_CONTRACT_BRANCH
    {
        const std::string u = studentecho_upper_contract(rest);
        if (u == "USAGE" || u == "HELP" || u == "?") {
            print_studentecho_usage_contract();
            return;
        }
    }
    if (rest.empty()) {
        print_studentecho_usage_contract();
        return;
    }

    std::cout << rest << "\n";
}

static bool s_registered = []() {
    dli::register_extension_command("STUDENTECHO",
        [](xbase::DbArea& A, std::istringstream& S) {
            cmd_STUDENTECHO(A, S);
            relations_api::refresh_if_enabled();
        },
        "src/ext/cmd/cmd_student_echo.cpp");

    dli::register_extension_command("SECHO",
        [](xbase::DbArea& A, std::istringstream& S) {
            cmd_STUDENTECHO(A, S);
            relations_api::refresh_if_enabled();
        },
        "src/ext/cmd/cmd_student_echo.cpp");

    return true;
}();

} // namespace
