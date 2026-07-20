// @dottalk.usage v1
// owner: DOT|SKIP
// command: SKIP
// category: navigation
// status: supported
// noargs: navigate
// effect: navigate
// mutates: cursor
// usage-access: SKIP USAGE
// summary:
//   Move the current work-area cursor forward or backward using filter-aware
//   navigation selection.
//
// usage:
//   SKIP
//   SKIP USAGE
//   SKIP <n>
//
// notes:
//   SKIP with no arguments moves forward one logical record.
//   SKIP <n> moves forward when n is positive and backward when n is negative.
//   SKIP 0 rereads the current record.
//   SKIP requires an open table except for SKIP USAGE.
//   Navigation uses the shared filter-aware selector.
//   SKIP mutates cursor position but does not mutate table data.
//
// risk:
//   mutates_cursor: yes
//   mutates_table_data: no
//   requires_open_table: yes except usage
//
// related:
//   GOTO
//   TOP
//   BOTTOM
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
static std::string skip_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string skip_upper(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static bool is_skip_usage_request(const std::string& raw)
{
    std::string t = skip_upper(skip_trim(raw));
    if (t.rfind("SKIP ", 0) == 0) {
        t = skip_upper(skip_trim(t.substr(5)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_skip_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::SkipUsageText);
}
} // namespace

void cmd_SKIP(xbase::DbArea& A, std::istringstream& in)
{
    const std::string raw_args = in.str();
    if (is_skip_usage_request(raw_args)) {
        print_skip_usage();
        return;
    }

    if (!A.isOpen()) {
        cli::cmdout::print_prefixed_message("SKIP", dottalk::helpdata::MessageId::NavNoFileOpenText);
        return;
    }

    int n = 1;
    if (!(in >> n)) {
        n = 1;
    }

    const bool talk = cli::Settings::instance().talk_on.load();

    if (n == 0) {
        if (!A.readCurrent()) {
            cli::cmdout::print_prefixed_message("SKIP", dottalk::helpdata::MessageId::NavReadCurrentFailedText);
            return;
        }
        if (talk) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::NavRecnoLine,
                {{"recno", std::to_string(A.recno())}});
        }
        return;
    }

    // Fast path: an unfiltered ordered SKIP performs the whole delta on a single
    // index cursor (one seek + N advances) instead of N re-seeking unit steps.
    // order_skip() moves up to |n| positions (partial-to-boundary) and leaves the
    // work area positioned and read. The per-record visibility loop below runs
    // only when a SET FILTER is active (which needs per-candidate visibility).
    if (!filter::has_active_filter(&A) && orderstate::hasOrder(A)) {
        if (order_skip(A, n)) {
            if (talk) {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::NavRecnoLine,
                    {{"recno", std::to_string(A.recno())}});
            }
            return;
        }
        // Could not move -> already at the order boundary.
        cli::cmdout::print_prefixed_message("SKIP", dottalk::helpdata::MessageId::NavAtEndText);
        return;
    }

    int steps = (n >= 0 ? n : -n);
    const auto step_kind = (n >= 0)
        ? cli::navsel::Step::Next
        : cli::navsel::Step::Prior;

    int32_t current = A.recno();
    int32_t rn = 0;
    bool moved = false;

    while (steps-- > 0) {
        rn = cli::navsel::pick_recno(
            A,
            cli::navsel::Mode::AutoByFilter,
            step_kind,
            current);

        if (rn <= 0) {
            if (!moved) {
                cli::cmdout::print_prefixed_message("SKIP", dottalk::helpdata::MessageId::NavAtEndText);
                return;
            }
            break;
        }

        current = rn;
        moved = true;
    }

    if (!moved || !A.gotoRec(current) || !A.readCurrent()) {
        cli::cmdout::print_prefixed_message("SKIP", dottalk::helpdata::MessageId::NavFailedText);
        return;
    }

    if (talk) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::NavRecnoLine,
            {{"recno", std::to_string(A.recno())}});
    }
}
