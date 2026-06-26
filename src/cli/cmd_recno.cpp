// src/cli/cmd_recno.cpp
// @dottalk.usage v1
// owner: DOT|RECNO
// command: RECNO
// category: navigation
// status: supported
// noargs: report
// effect: mixed
// mutates: cursor
// usage-access: RECNO USAGE
// summary:
//   Report the current record number or navigate to an explicit record number.
//
// usage:
//   RECNO
//   RECNO USAGE
//   RECNO <n>
//
// notes:
//   RECNO with no arguments reports the current record number.
//   RECNO <n> navigates to record n and prints the resulting record number.
//   RECNO requires an open table except for RECNO USAGE.
//   RECNO mutates cursor position only when a numeric record argument is supplied.
//
// risk:
//   reads_cursor: yes
//   mutates_cursor: RECNO <n>
//   mutates_table_data: no
//   requires_open_table: yes except usage
//
// related:
//   GOTO
//   GPS
//   SKIP
//

#include "xbase.hpp"
#include "cli/command_output.hpp"
#include "help/helpdata_messages.hpp"
#include "textio.hpp"

#include <string>
#include <sstream>
#include <cctype>
#include <limits>
#include <cstdlib>
#include <algorithm>


static std::string recno_upper(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool is_recno_usage_request(std::string raw) {
    std::string t = recno_upper(textio::trim(std::move(raw)));
    if (t.rfind("RECNO ", 0) == 0) {
        t = recno_upper(textio::trim(t.substr(6)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_recno_usage() {
    cli::cmdout::print_message(dottalk::helpdata::MessageId::RecnoUsageText);
}

static bool parse_int32(const std::string& s, int32_t& out) {
    if (s.empty()) return false;
    char* end = nullptr;
    long v = std::strtol(s.c_str(), &end, 10);
    if (*end != '\0') return false;
    if (v < std::numeric_limits<int32_t>::min() || v > std::numeric_limits<int32_t>::max()) return false;
    out = static_cast<int32_t>(v);
    return true;
}

void cmd_RECNO(xbase::DbArea& a, std::istringstream& iss) {
    const std::string raw_args = iss.str();
    if (is_recno_usage_request(raw_args)) {
        print_recno_usage();
        return;
    }

    std::string tok;
    if (!(iss >> tok)) {
        tok.clear();
    } else if (recno_upper(tok) == "RECNO") {
        tok.clear();
    }

    if (!a.isOpen()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::NoOpenTable);
        return;
    }

    if (tok.empty()) {
        // no args: print current recno
        cli::cmdout::print_line(std::to_string(a.recno()));
        return;
    }

    int32_t n = 0;
    if (!parse_int32(tok, n)) { print_recno_usage(); return; }

    if (n < 1 || n > a.recCount()) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::RecnoOutOfRangeText,
            {{"max", std::to_string(a.recCount())}});
        return;
    }

    if (!a.gotoRec(n) || !a.readCurrent()) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::RecnoUnableNavigateText,
            {{"recno", std::to_string(n)}});
        return;
    }

    cli::cmdout::print_line(std::to_string(a.recno()));
}



