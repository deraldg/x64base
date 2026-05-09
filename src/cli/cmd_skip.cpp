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
#include <iostream>
#include <cstdint>

#include "xbase.hpp"
#include "cli/nav_select.hpp"
#include "cli/settings.hpp"


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
    std::cout
        << "Usage:\n"
        << "  SKIP\n"
        << "  SKIP USAGE\n"
        << "  SKIP <n>\n";
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
        std::cout << "SKIP: no file open.\n";
        return;
    }

    int n = 1;
    if (!(in >> n)) {
        n = 1;
    }

    const bool talk = cli::Settings::instance().talk_on.load();

    if (n == 0) {
        if (!A.readCurrent()) {
            std::cout << "SKIP: failed to read record.\n";
            return;
        }
        if (talk) std::cout << "Recno: " << A.recno() << "\n";
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
                std::cout << "SKIP: at end.\n";
                return;
            }
            break;
        }

        current = rn;
        moved = true;
    }

    if (!moved || !A.gotoRec(current) || !A.readCurrent()) {
        std::cout << "SKIP: failed.\n";
        return;
    }

    if (talk) std::cout << "Recno: " << A.recno() << "\n";
}
