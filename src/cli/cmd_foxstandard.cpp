// src/cli/cmd_foxstandard.cpp
//
// FOXSTANDARD is a static historical reference command.
// It is intentionally separate from live HELP and the live command catalogs.

// @dottalk.usage v1
// owner: DOT|FOXSTANDARD
// command: FOXSTANDARD
// category: help
// status: supported
// noargs: usage
// effect: report
// mutates: none
// usage-access: FOXSTANDARD USAGE
// summary:
//   Render static historical FoxPro-standard reference topics.
//
// usage:
//   FOXSTANDARD USAGE
//   FOXSTANDARD <command>
//   FOXSTANDARD ALL
//   FOXSTANDARD TOPICS
//   FOXSTANDARD LIST
//
// notes:
//   FOXSTANDARD with no arguments shows usage.
//   FOXSTANDARD ALL, TOPICS, and LIST render the available topic list.
//   FOXSTANDARD <command> renders the static reference for that command.
//   FOXSTANDARD is separate from the live HELP and command catalogs.
//
// risk:
//   reads_static_reference: yes
//   mutates_table_data: no
//   mutates_session: no
//
// related:
//   FOXHELP
//   HELP
//   CMDHELP
//

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


void print_foxstandard_usage()
{
    std::cout
        << "Usage:\n"
        << "  FOXSTANDARD USAGE\n"
        << "  FOXSTANDARD <command>\n"
        << "  FOXSTANDARD ALL\n"
        << "  FOXSTANDARD TOPICS\n"
        << "  FOXSTANDARD LIST\n";
}

} // namespace

void cmd_FOXSTANDARD(xbase::DbArea& area, std::istringstream& iss)
{
    (void)area;

    std::string rest;
    std::getline(iss, rest);
    rest = trim_copy(rest);

    const std::string topic_upper = upper_copy(rest);

    if (rest.empty() || topic_upper == "USAGE" || topic_upper == "HELP" || topic_upper == "?") {
        print_foxstandard_usage();
        return;
    }


    if (topic_upper == "ALL" || topic_upper == "TOPICS" || topic_upper == "LIST") {
        std::cout << dottalk::foxstd::render_topic_list();
        return;
    }

    std::cout << dottalk::foxstd::render_doc(rest) << "\n";
}
