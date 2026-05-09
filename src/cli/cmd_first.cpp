// src/cli/cmd_first.cpp
// FIRST = first visible record in current logical view
// (active order + filter visibility).

// @dottalk.usage v1
// owner: DOT|FIRST
// command: FIRST
// category: navigation
// status: supported
// noargs: navigate
// effect: navigate
// mutates: cursor
// usage-access: FIRST USAGE
// summary:
//   Move the current work-area cursor to the first visible/logical record.
//
// usage:
//   FIRST
//   FIRST USAGE
//
// notes:
//   FIRST with no arguments moves to the first visible/logical record.
//   FIRST requires an open table except for FIRST USAGE.
//   FIRST uses the logical_nav first_recno helper.
//   FIRST mutates cursor position but does not mutate table data.
//   TALK ON prints the resulting record number when movement succeeds.
//
// risk:
//   mutates_cursor: yes
//   mutates_table_data: no
//   requires_open_table: yes except usage
//
// related:
//   TOP
//   BOTTOM
//   FIRST
//   LAST
//   NEXT
//   PRIOR
//   SKIP
//   GOTO
//   GPS
//

#include <sstream>
#include <iostream>
#include <cstdint>

#include "xbase.hpp"
#include "cli/logical_nav.hpp"
#include "cli/settings.hpp"
#include <algorithm>
#include <cctype>
#include <string>


namespace {
static std::string first_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string first_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool is_first_usage_request(const std::string& raw)
{
    std::string t = first_upper(first_trim(raw));
    if (t.rfind("FIRST ", 0) == 0) {
        t = first_upper(first_trim(t.substr(6)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_first_usage()
{
    std::cout
        << "Usage:\n"
        << "  FIRST\n"
        << "  FIRST USAGE\n";
}
} // namespace

void cmd_FIRST(xbase::DbArea& A, std::istringstream& in)
{
    const std::string raw_args = in.str();
    if (is_first_usage_request(raw_args)) {
        print_first_usage();
        return;
    }

    if (!A.isOpen()) {
        std::cout << "FIRST: no file open.\n";
        return;
    }

    const int32_t rn = cli::logical_nav::first_recno(A);
    if (rn <= 0) {
        std::cout << "FIRST: failed.\n";
        return;
    }

    if (!A.gotoRec(rn) || !A.readCurrent()) {
        std::cout << "FIRST: failed.\n";
        return;
    }

    if (cli::Settings::instance().talk_on.load()) {
        std::cout << "Recno: " << A.recno() << "\n";
    }
}
