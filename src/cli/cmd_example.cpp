// @dottalk.usage v1
// owner: DOT|EXAMPLE
// command: EXAMPLE
// category: diagnostics
// status: supported
// noargs: usage
// effect: test
// mutates: none
// usage-access: EXAMPLE USAGE
// summary:
//   Minimal example/test command used to verify token parsing and command routing.
//
// usage:
//   EXAMPLE USAGE
//   EXAMPLE TEST
//
// notes:
//   EXAMPLE with no arguments shows usage.
//   EXAMPLE TEST prints OK.
//   EXAMPLE is read-only and does not mutate table data.
//
// risk:
//   mutates_table_data: no
//
// related:
//   ERROR_TEST
//   TEST
//

#include "xbase.hpp"
#include "textio.hpp"

#include <iostream>
#include <sstream>
#include <string>

void cmd_EXAMPLE(xbase::DbArea&, std::istringstream& iss)
{
    auto toks = textio::tokenize(iss);

    const std::string a1 = toks.size() > 0 ? textio::upper(toks[0]) : "";

    if (a1 == "TEST")
    {
        std::cout << "OK\n";
        return;
    }

    std::cout << "Usage:\n  EXAMPLE USAGE\n  EXAMPLE TEST\n";
}