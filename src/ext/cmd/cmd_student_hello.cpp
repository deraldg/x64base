// @dottalk.usage v1
// owner: EXT|STUDENTHELLO
// command: STUDENTHELLO / SHELLO
// category: extension-example
// status: sample-extension
// noargs: greeting-plus-usage
// effect: report
// mutates: none
// usage-access: STUDENTHELLO USAGE; SHELLO USAGE
// summary:
//   Student/custom extension sample that greets a supplied name or message.
//
// usage:
//   STUDENTHELLO USAGE
//   STUDENTHELLO <name-or-message>
//   SHELLO USAGE
//   SHELLO <name-or-message>
//
// examples:
//   STUDENTHELLO Derald
//   SHELLO class
//
// notes:
//   Usage/help/? prints usage before greeting output.
//   No-argument behavior keeps the existing sample greeting plus usage.
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

    This file is a student/custom extension example.

    - Built-in CLI commands are centrally registered in the protected shell/bootstrap path.
    - Custom CLI commands may self-register from the extension area.
    - Do not use built-in command names here.
    - If this file is removed from the build, the command disappears. That is expected.

    This sample adds:
        STUDENTHELLO
        SHELLO
*/

namespace {

static std::string studenthello_upper_contract(std::string s)
{
    for (char& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

static void print_studenthello_usage_contract()
{
    std::cout
        << "Usage:\n"
        << "  STUDENTHELLO USAGE\n"
        << "  STUDENTHELLO <name-or-message>\n"
        << "  SHELLO USAGE\n"
        << "  SHELLO <name-or-message>\n"
        << "Examples:\n"
        << "  STUDENTHELLO Derald\n"
        << "  SHELLO class\n"
        << "Notes:\n"
        << "  - USAGE/HELP/? does not print a greeting.\n";
}
void cmd_STUDENTHELLO(xbase::DbArea&, std::istringstream& in)
{
    std::string rest;
    std::getline(in, rest);

    if (!rest.empty() && rest.front() == ' ') {
        rest.erase(rest.begin());
    }

    // STUDENTHELLO_USAGE_CONTRACT_BRANCH
    {
        const std::string u = studenthello_upper_contract(rest);
        if (u == "USAGE" || u == "HELP" || u == "?") {
            print_studenthello_usage_contract();
            return;
        }
    }
    if (rest.empty()) {
        std::cout << "Hello from the student extension system.\n";
        print_studenthello_usage_contract();
        return;
    }

    std::cout << "Hello, " << rest << ".\n";
}

static bool s_registered = []() {
    dli::register_extension_command("STUDENTHELLO",
        [](xbase::DbArea& A, std::istringstream& S) {
            cmd_STUDENTHELLO(A, S);
            relations_api::refresh_if_enabled();
        },
        "src/ext/cmd/cmd_student_hello.cpp");

    dli::register_extension_command("SHELLO",
        [](xbase::DbArea& A, std::istringstream& S) {
            cmd_STUDENTHELLO(A, S);
            relations_api::refresh_if_enabled();
        },
        "src/ext/cmd/cmd_student_hello.cpp");

    return true;
}();

} // namespace
