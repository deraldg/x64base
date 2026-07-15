// src/cli/cmd_select.cpp ? SELECT <area#|name>
// Supports selecting by numeric slot (0..N-1) or by name/label (case-insensitive).
// Name matching checks workareas::name(i) and the DBF base name from DbArea::filename().
//
// Output style (matches your UX):
//   Selected area 9.
//   Current area: 9
//     File: <path>  Recs: <count>  Recno: <current>
//
// Deps: workareas.hpp, xbase.hpp

// @dottalk.usage v1
// owner: DOT|SELECT
// command: SELECT
// category: workspace
// status: supported
// noargs: usage
// effect: select
// mutates: current-area
// usage-access: SELECT USAGE
// summary:
//   Select the current work area by numeric slot or by work-area/table name.
//
// usage:
//   SELECT USAGE
//   SELECT <n>
//   SELECT <name>
//   SELECT <table.dbf>
//
// notes:
//   SELECT with no arguments prints usage with the current valid slot range.
//   SELECT USAGE prints usage and does not change the current area.
//   Numeric selection uses the current workarea slot count.
//   Name selection matches workarea labels and open DBF base names case-insensitively.
//   SELECT mutates current-area/session state but does not mutate table data.
//
// risk:
//   mutates_current_area: yes
//   mutates_table_data: no
//
// related:
//   AREA
//   DBAREA
//   WORKSPACE
//

#include <string>
#include <sstream>
#include <iostream>
#include <algorithm>
#include <cctype>
#include <limits>

#include "cli/command_output.hpp"
#include "help/helpdata_messages.hpp"
#include "xbase.hpp"
#include "workareas.hpp"

// Provided by the shell (C linkage there)
extern "C" xbase::XBaseEngine* shell_engine();

// ----------------- helpers -----------------

static std::string to_upper(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c){ return (char)std::toupper(c); });
    return s;
}

static std::string base_name_upper_from_cstr(const char* pathLike) {
    if (!pathLike) return {};
    std::string s(pathLike);
    for (char& c : s) if (c == '\\') c = '/';
    if (auto pos = s.find_last_of('/'); pos != std::string::npos) s.erase(0, pos + 1);
    std::string S = to_upper(s);
    const std::string ext = ".DBF";
    if (S.size() >= ext.size() && S.substr(S.size() - ext.size()) == ext) {
        S.erase(S.size() - ext.size());
    }
    return S;
}

static std::string base_name_upper_from_str(const std::string& pathLike) {
    return base_name_upper_from_cstr(pathLike.c_str());
}

static bool try_parse_int(const std::string& s, int& out) {
    if (s.empty()) return false;
    size_t i = 0;
    if (s[0] == '+' || s[0] == '-') i = 1;
    for (; i < s.size(); ++i)
        if (!std::isdigit(static_cast<unsigned char>(s[i]))) return false;
    try {
        long long v = std::stoll(s);
        if (v < std::numeric_limits<int>::min() || v > std::numeric_limits<int>::max()) return false;
        out = static_cast<int>(v);
        return true;
    } catch (...) { return false; }
}

// ----------------- command -----------------

static void print_select_usage()
{
    const size_t cnt = workareas::count();
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::SelectUsageText,
        {{"max_slot", std::to_string(cnt ? static_cast<int>(cnt - 1) : 0)}});
}

void cmd_SELECT(xbase::DbArea& /*A*/, std::istringstream& iss) {
    xbase::XBaseEngine* eng = shell_engine();
    if (!eng) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::SelectEngineUnavailableText);
        return;
    }

    std::string arg;
    if (!(iss >> arg) || arg.empty()) {
        print_select_usage();
        return;
    }

    const std::string argU0 = to_upper(arg);
    if (argU0 == "USAGE" || argU0 == "HELP" || argU0 == "?") {
        print_select_usage();
        return;
    }

    // Allow quoted names
    if (arg.size() >= 2 && ((arg.front() == '"' && arg.back() == '"') ||
                            (arg.front() == '\'' && arg.back() == '\''))) {
        arg = arg.substr(1, arg.size() - 2);
    }

    int idx = -1;

    // numeric?
    int nParsed = -1;
    if (try_parse_int(arg, nParsed)) {
        const size_t cnt = workareas::count();
        if (nParsed < 0 || (size_t)nParsed >= cnt) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::SelectOutOfRangeText,
                {{"max_slot", std::to_string(cnt ? static_cast<int>(cnt - 1) : 0)}});
            return;
        }
        idx = nParsed;
    } else {
        // name/label (case-insensitive), accept with/without .DBF
        std::string wantU = to_upper(arg);
        std::string wantBase = wantU;
        if (wantBase.size() > 4 && wantBase.substr(wantBase.size() - 4) == ".DBF") {
            wantBase.erase(wantBase.size() - 4);
        }

        for (size_t i = 0; i < workareas::count(); ++i) {
            const char* label = workareas::name(i);
            std::string labU   = to_upper(label ? std::string(label) : std::string());
            std::string labBase= base_name_upper_from_cstr(label);

            if ((!labU.empty() && labU == wantU) || (!labBase.empty() && labBase == wantBase)) {
                idx = (int)i;
                break;
            }

            // Fallback: if open, try the filename() base
            const xbase::DbArea* a = workareas::db(i);
            if (a && a->isOpen()) {
                std::string fileBase = base_name_upper_from_str(a->filename());
                if (!fileBase.empty() && fileBase == wantBase) {
                    idx = (int)i;
                    break;
                }
            }
        }

        if (idx < 0) {
            const size_t cnt = workareas::count();
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::SelectNoAreaMatchesText,
                {
                    {"name", arg},
                    {"max_slot", std::to_string(cnt ? static_cast<int>(cnt - 1) : 0)}
                });
            return;
        }
    }

    // Perform selection & echo
    eng->selectArea((size_t)idx);
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::SelectSelectedAreaText,
        {{"slot", std::to_string(idx)}});

    const xbase::DbArea* cur = workareas::db((size_t)idx);
    if (cur && cur->isOpen()) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SelectCurrentAreaText,
            {{"slot", std::to_string(idx)}});
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SelectCurrentAreaFileSummaryText,
            {
                {"path", cur->filename()},
                {"recs", std::to_string(cur->recCount())},
                {"recno", std::to_string(cur->recno())}
            });
    } else {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SelectCurrentAreaText,
            {{"slot", std::to_string(idx)}});
    }
}




