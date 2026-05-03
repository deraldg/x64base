// src/cli/cmd_foxstandard.cpp
//
// FOXSTANDARD is a static historical reference command.
// It is intentionally separate from live HELP and the live command catalogs.

#include "fox_standard_render.hpp"
#include "xbase.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>

namespace {

std::string trim_copy(std::string s)
{
    const auto first = s.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) {
        return {};
    }

    const auto last = s.find_last_not_of(" \t\r\n");
    return s.substr(first, last - first + 1);
}

std::string upper_copy(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c) {
            return static_cast<char>(std::toupper(c));
        });
    return s;
}

} // namespace

void cmd_FOXSTANDARD(xbase::DbArea& area, std::istringstream& iss)
{
    (void)area;

    std::string rest;
    std::getline(iss, rest);
    rest = trim_copy(rest);

    if (rest.empty()) {
        std::cout << "Usage: FOXSTANDARD <command|ALL>\n";
        return;
    }

    const std::string topic_upper = upper_copy(rest);

    if (topic_upper == "ALL" || topic_upper == "TOPICS" || topic_upper == "LIST") {
        std::cout << dottalk::foxstd::render_topic_list();
        return;
    }

    std::cout << dottalk::foxstd::render_doc(rest) << "\n";
}
