// src/cli/cmd_goto.cpp
// Narrow, engine-facing GOTO command.
//
// Supported forms:
//   GOTO <recno>
//   GOTO FIRST
//   GOTO LAST

// @dottalk.usage v1
// owner: DOT|GOTO
// command: GOTO
// category: navigation
// status: supported
// noargs: usage
// effect: navigate
// mutates: cursor
// usage-access: GOTO USAGE
// summary:
//   Move the current work-area cursor to an absolute record number, first
//   record, or last record through the shared navigation layer.
//
// usage:
//   GOTO USAGE
//   GOTO <recno>
//   GOTO FIRST
//   GOTO LAST
//
// notes:
//   GOTO requires a target argument except for GOTO USAGE.
//   GOTO FIRST and GOTO LAST use endpoint navigation.
//   GOTO <recno> uses absolute record navigation.
//   GOTO mutates cursor position but does not mutate table data.
//
// risk:
//   mutates_cursor: yes
//   mutates_table_data: no
//   requires_open_table: navigation layer dependent
//
// related:
//   SKIP
//   GO
//   TOP
//   BOTTOM
//   GPS
//

#include <cctype>
#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "cli/nav_move.hpp"


namespace {
static std::string goto_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string goto_upper(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static bool is_goto_usage_request(const std::string& raw)
{
    std::string t = goto_upper(goto_trim(raw));
    if (t.rfind("GOTO ", 0) == 0) {
        t = goto_upper(goto_trim(t.substr(5)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_goto_usage()
{
    std::cout
        << "Usage:\n"
        << "  GOTO USAGE\n"
        << "  GOTO <recno>\n"
        << "  GOTO FIRST\n"
        << "  GOTO LAST\n";
}
} // namespace

void cmd_GOTO(xbase::DbArea& A, std::istringstream& iss)
{
    const std::string raw_args = iss.str();
    if (is_goto_usage_request(raw_args)) {
        print_goto_usage();
        return;
    }

    std::string tok;
    if (!(iss >> tok)) {
        print_goto_usage();
        return;
    }

    const std::string u = cli::nav::upper_copy(tok);
    if (u == "FIRST") {
        cli::nav::go_endpoint(A, cli::nav::Endpoint::First, "GOTO");
        return;
    }
    if (u == "LAST") {
        cli::nav::go_endpoint(A, cli::nav::Endpoint::Last, "GOTO");
        return;
    }

    int n = 0;
    if (!cli::nav::try_parse_int_token(tok, n) || n <= 0) {
        print_goto_usage();
        return;
    }

    cli::nav::go_absolute(A, n, "GOTO");
}
