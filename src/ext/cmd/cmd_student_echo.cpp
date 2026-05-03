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

void cmd_STUDENTECHO(xbase::DbArea&, std::istringstream& in)
{
    std::string rest;
    std::getline(in, rest);

    if (!rest.empty() && rest.front() == ' ') {
        rest.erase(rest.begin());
    }

    if (rest.empty()) {
        std::cout << "Usage: STUDENTECHO <text>\n";
        return;
    }

    std::cout << rest << "\n";
}

static bool s_registered = []() {
    dli::registry().add("STUDENTECHO",
        [](xbase::DbArea& A, std::istringstream& S) {
            cmd_STUDENTECHO(A, S);
            relations_api::refresh_if_enabled();
        });

    dli::registry().add("SECHO",
        [](xbase::DbArea& A, std::istringstream& S) {
            cmd_STUDENTECHO(A, S);
            relations_api::refresh_if_enabled();
        });

    return true;
}();

} // namespace
