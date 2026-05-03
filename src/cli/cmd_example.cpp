#include "xbase.hpp"
#include "textio.hpp"

#include <iostream>
#include <sstream>
#include <string>

void cmd_EXAMPLE(xbase::DbArea&, std::istringstream& iss)
{
    auto toks = textio::tokenize(iss);

    const std::string a1 = toks.size() > 0 ? textio::upper(toks[0]) : "";
    const std::string a2 = toks.size() > 1 ? toks[1] : "";

    if (a1 == "TEST")
    {
        std::cout << "OK\n";
        return;
    }

    std::cout << "Usage: EXAMPLE TEST\n";
}