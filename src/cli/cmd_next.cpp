// src/cli/cmd_next.cpp
// NEXT = next visible record in current logical view
// (active order + filter visibility).

// @dottalk.usage v1
// owner: DOT|NEXT
// command: NEXT
// category: navigation
// status: supported
// noargs: navigate
// effect: navigate
// mutates: cursor
// usage-access: NEXT USAGE
// summary:
//   Move the current work-area cursor to the next visible/logical record.
//
// usage:
//   NEXT
//   NEXT USAGE
//
// notes:
//   NEXT with no arguments moves to the next visible/logical record.
//   NEXT requires an open table except for NEXT USAGE.
//   NEXT uses the logical_nav next_recno helper.
//   NEXT mutates cursor position but does not mutate table data.
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
#include <cstdint>

#include "cli/command_output.hpp"
#include "xbase.hpp"
#include "cli/logical_nav.hpp"
#include "cli/settings.hpp"
#include <algorithm>
#include <cctype>
#include <string>
#include "help/helpdata_messages.hpp"


namespace {
static std::string next_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string next_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool is_next_usage_request(const std::string& raw)
{
    std::string t = next_upper(next_trim(raw));
    if (t.rfind("NEXT ", 0) == 0) {
        t = next_upper(next_trim(t.substr(5)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_next_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::NextUsageText);
}
} // namespace

void cmd_NEXT(xbase::DbArea& A, std::istringstream& in)
{
    const std::string raw_args = in.str();
    if (is_next_usage_request(raw_args)) {
        print_next_usage();
        return;
    }

    if (!A.isOpen()) {
        cli::cmdout::print_prefixed_message("NEXT", dottalk::helpdata::MessageId::NavNoFileOpenText);
        return;
    }

    const int32_t rn = cli::logical_nav::next_recno(A, A.recno());
    if (rn <= 0) {
        cli::cmdout::print_prefixed_message("NEXT", dottalk::helpdata::MessageId::NavAtEndText);
        return;
    }

    if (!A.gotoRec(rn) || !A.readCurrent()) {
        cli::cmdout::print_prefixed_message("NEXT", dottalk::helpdata::MessageId::NavFailedText);
        return;
    }

    if (cli::Settings::instance().talk_on.load()) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::NavRecnoLine,
            {{"recno", std::to_string(A.recno())}});
    }
}
