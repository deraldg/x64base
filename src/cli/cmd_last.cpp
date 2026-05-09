// src/cli/cmd_last.cpp
// LAST = last visible record in current logical view
// (active order + filter visibility).

// @dottalk.usage v1
// owner: DOT|LAST
// command: LAST
// category: navigation
// status: supported
// noargs: navigate
// effect: navigate
// mutates: cursor
// usage-access: LAST USAGE
// summary:
//   Move the current work-area cursor to the last visible/logical record.
//
// usage:
//   LAST
//   LAST USAGE
//
// notes:
//   LAST with no arguments moves to the last visible/logical record.
//   LAST requires an open table except for LAST USAGE.
//   LAST uses the logical_nav last_recno helper.
//   LAST mutates cursor position but does not mutate table data.
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
static std::string last_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string last_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool is_last_usage_request(const std::string& raw)
{
    std::string t = last_upper(last_trim(raw));
    if (t.rfind("LAST ", 0) == 0) {
        t = last_upper(last_trim(t.substr(5)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_last_usage()
{
    std::cout
        << "Usage:\n"
        << "  LAST\n"
        << "  LAST USAGE\n";
}
} // namespace

void cmd_LAST(xbase::DbArea& A, std::istringstream& in)
{
    const std::string raw_args = in.str();
    if (is_last_usage_request(raw_args)) {
        print_last_usage();
        return;
    }

    if (!A.isOpen()) {
        std::cout << "LAST: no file open.\n";
        return;
    }

    const int32_t rn = cli::logical_nav::last_recno(A);
    if (rn <= 0) {
        std::cout << "LAST: failed.\n";
        return;
    }

    if (!A.gotoRec(rn) || !A.readCurrent()) {
        std::cout << "LAST: failed.\n";
        return;
    }

    if (cli::Settings::instance().talk_on.load()) {
        std::cout << "Recno: " << A.recno() << "\n";
    }
}
