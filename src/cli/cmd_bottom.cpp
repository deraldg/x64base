// @dottalk.usage v1
// owner: DOT|BOTTOM
// command: BOTTOM
// category: navigation
// status: supported
// noargs: navigate
// effect: navigate
// mutates: cursor
// usage-access: BOTTOM USAGE
// summary:
//   Move the current work-area cursor to the last visible/logical record.
//
// usage:
//   BOTTOM
//   BOTTOM USAGE
//
// notes:
//   BOTTOM with no arguments moves to the last visible/logical record.
//   BOTTOM requires an open table except for BOTTOM USAGE.
//   BOTTOM uses the AutoByFilter last-record navigation selector.
//   BOTTOM mutates cursor position but does not mutate table data.
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
#include "cli/nav_select.hpp"
#include "cli/settings.hpp"
#include <algorithm>
#include <cctype>
#include <string>
#include "help/helpdata_messages.hpp"


namespace {
static std::string bottom_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string bottom_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool is_bottom_usage_request(const std::string& raw)
{
    std::string t = bottom_upper(bottom_trim(raw));
    if (t.rfind("BOTTOM ", 0) == 0) {
        t = bottom_upper(bottom_trim(t.substr(7)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_bottom_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::BottomUsageText);
}
} // namespace

void cmd_BOTTOM(xbase::DbArea& A, std::istringstream& in)
{
    const std::string raw_args = in.str();
    if (is_bottom_usage_request(raw_args)) {
        print_bottom_usage();
        return;
    }

    if (!A.isOpen()) {
        cli::cmdout::print_prefixed_message("BOTTOM", dottalk::helpdata::MessageId::NavNoFileOpenText);
        return;
    }

    const int32_t rn = cli::navsel::pick_recno(
        A,
        cli::navsel::Mode::AutoByFilter,
        cli::navsel::Step::Last);

    if (rn <= 0 || !A.gotoRec(rn) || !A.readCurrent()) {
        cli::cmdout::print_prefixed_message("BOTTOM", dottalk::helpdata::MessageId::NavFailedText);
        return;
    }

    if (cli::Settings::instance().talk_on.load()) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::NavRecnoLine,
            {{"recno", std::to_string(A.recno())}});
    }
}
