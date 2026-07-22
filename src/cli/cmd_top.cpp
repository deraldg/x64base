// @dottalk.usage v1
// owner: DOT|TOP
// command: TOP
// category: navigation
// status: supported
// noargs: navigate
// effect: navigate
// mutates: cursor
// usage-access: TOP USAGE
// summary:
//   Move the current work-area cursor to the first visible/logical record using
//   the shared filter-aware navigation selector.
//
// usage:
//   TOP
//   TOP USAGE
//
// notes:
//   TOP with no arguments moves to the first visible record.
//   TOP requires an open table except for TOP USAGE.
//   TOP mutates cursor position but does not mutate table data.
//   TALK ON prints the resulting record number.
//
// risk:
//   mutates_cursor: yes
//   mutates_table_data: no
//   requires_open_table: yes except usage
//
// related:
//   BOTTOM
//   SKIP
//   GOTO
//   GPS
//

#include <cctype>
#include <sstream>
#include <cstdint>

#include "cli/command_output.hpp"
#include "xbase.hpp"
#include "cli/nav_select.hpp"
#include "cli/settings.hpp"
#include "help/helpdata_messages.hpp"


namespace {
static std::string top_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string top_upper(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static bool is_top_usage_request(const std::string& raw)
{
    std::string t = top_upper(top_trim(raw));
    if (t.rfind("TOP ", 0) == 0) {
        t = top_upper(top_trim(t.substr(4)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_top_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::TopUsageText);
}
} // namespace

void cmd_TOP(xbase::DbArea& A, std::istringstream& in)
{
    const std::string raw_args = in.str();
    if (is_top_usage_request(raw_args)) {
        print_top_usage();
        return;
    }

    if (!A.isOpen()) {
        cli::cmdout::print_prefixed_message("TOP", dottalk::helpdata::MessageId::NavNoFileOpenText);
        return;
    }

    const std::int64_t rn = cli::navsel::pick_recno(
        A,
        cli::navsel::Mode::AutoByFilter,
        cli::navsel::Step::First);

    if (rn <= 0 || !A.gotoRec64(static_cast<std::uint64_t>(rn)) || !A.readCurrent()) {
        cli::cmdout::print_prefixed_message("TOP", dottalk::helpdata::MessageId::NavFailedText);
        return;
    }

    if (cli::Settings::instance().talk_on.load()) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::NavRecnoLine,
            {{"recno", std::to_string(A.recno())}});
    }
}
