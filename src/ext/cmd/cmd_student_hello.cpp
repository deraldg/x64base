#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "set_relations.hpp"
#include "cli/command_registry.hpp"
#include "../ext_policy.hpp"

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

void cmd_STUDENTHELLO(xbase::DbArea&, std::istringstream& in)
{
    std::string rest;
    std::getline(in, rest);

    if (!rest.empty() && rest.front() == ' ') {
        rest.erase(rest.begin());
    }

    if (rest.empty()) {
        std::cout << "Hello from the student extension system.\n";
        std::cout << "Usage: STUDENTHELLO <name-or-message>\n";
        return;
    }

    std::cout << "Hello, " << rest << ".\n";
}

static bool s_registered = []() {
    dli::registry().add("STUDENTHELLO",
        [](xbase::DbArea& A, std::istringstream& S) {
            cmd_STUDENTHELLO(A, S);
            relations_api::refresh_if_enabled();
        });

    dli::registry().add("SHELLO",
        [](xbase::DbArea& A, std::istringstream& S) {
            cmd_STUDENTHELLO(A, S);
            relations_api::refresh_if_enabled();
        });

    return true;
}();

} // namespace
