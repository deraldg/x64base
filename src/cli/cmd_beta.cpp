// @dottalk.usage v1
// owner: DOT|BETA
// command: BETA
// category: help
// status: supported
// noargs: report
// effect: mixed
// mutates: beta-status-overrides filesystem
// usage-access: BETA USAGE
// summary:
//   List, inspect, and update beta tracking items and runtime beta-status overrides.
//
// usage:
//   BETA
//   BETA USAGE
//   BETA LIST
//   BETA <id>
//   BETA DONE <id>
//   BETA DEFER <id>
//   BETA DEFERRED <id>
//   BETA OPEN <id>
//   BETA CLEAR <id>
//   BETA CLEAR ALL
//   BETA SAVE
//   BETA LOAD
//
// notes:
//   BETA with no arguments lists beta items.
//   BETA <id> shows a beta item when the id begins with BETA-.
//   DONE, DEFER, DEFERRED, OPEN, CLEAR, and CLEAR ALL mutate runtime beta status overrides.
//   SAVE writes beta status overrides to the default status path.
//   LOAD reads beta status overrides from the default status path.
//   BETA mutates only beta tracking/status data, not table records.
//
// risk:
//   mutates_beta_status: DONE DEFER DEFERRED OPEN CLEAR
//   reads_files: LOAD
//   writes_files: SAVE
//   mutates_table_data: no
//
// related:
//   ABOUT
//   HELP
//   FOXHELP
//

#include "foxref.hpp"
#include "help_beta.hpp"
#include "xbase.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>

namespace {

static std::string trim(std::string s)
{
    auto notsp = [](unsigned char c) { return !std::isspace(c); };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), notsp));
    s.erase(std::find_if(s.rbegin(), s.rend(), notsp).base(), s.end());
    return s;
}

static std::string upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return (char)std::toupper(c); });
    return s;
}

static void print_usage()
{
    std::cout
        << "Usage:\n"
        << "  BETA\n"
        << "  BETA USAGE\n"
        << "  BETA LIST\n"
        << "  BETA <ID>\n"
        << "  BETA DONE <ID>\n"
        << "  BETA DEFER <ID>\n"
        << "  BETA DEFERRED <ID>\n"
        << "  BETA OPEN <ID>\n"
        << "  BETA CLEAR <ID>\n"
        << "  BETA CLEAR ALL\n"
        << "  BETA SAVE\n"
        << "  BETA LOAD\n";
}

} // namespace

void cmd_BETA(xbase::DbArea& area, std::istringstream& args)
{
    (void)area; // currently unused, but keep standard handler signature

    std::string sub;
    args >> sub;
    sub = upper(trim(sub));

    if (sub.empty() || sub == "LIST") {
        dottalk::help::show_beta("");
        return;
    }

    // Detail lookup: BETA BETA-3.1
    if (sub.rfind("BETA-", 0) == 0) {
        dottalk::help::show_beta(sub);
        return;
    }

    if (sub == "DONE" || sub == "DEFER" || sub == "DEFERRED" || sub == "OPEN") {
        std::string id;
        args >> id;
        id = upper(trim(id));

        if (id.empty()) {
            print_usage();
            return;
        }

        const foxref::BetaItem* it = foxref::beta_find(id);
        if (!it) {
            std::cout << "BETA: unknown id: " << id << "\n";
            return;
        }

        if (sub == "DONE") {
            foxref::beta_set_status(it->id, foxref::BetaStatus::DONE);
            std::cout << "BETA " << it->id << " -> DONE\n";
            return;
        }

        if (sub == "DEFER" || sub == "DEFERRED") {
            foxref::beta_set_status(it->id, foxref::BetaStatus::DEFERRED);
            std::cout << "BETA " << it->id << " -> DEFERRED\n";
            return;
        }

        foxref::beta_set_status(it->id, foxref::BetaStatus::OPEN);
        std::cout << "BETA " << it->id << " -> OPEN\n";
        return;
    }

    if (sub == "CLEAR") {
        std::string what;
        args >> what;
        what = upper(trim(what));

        if (what.empty()) {
            print_usage();
            return;
        }

        if (what == "ALL") {
            foxref::beta_clear_all_status_overrides();
            std::cout << "BETA: all runtime overrides cleared\n";
            return;
        }

        const foxref::BetaItem* it = foxref::beta_find(what);
        if (!it) {
            std::cout << "BETA: unknown id: " << what << "\n";
            return;
        }

        foxref::beta_clear_status(it->id);
        std::cout << "BETA " << it->id << " override cleared\n";
        return;
    }

    if (sub == "SAVE") {
        std::string err;
        if (!foxref::beta_save_overrides(&err)) {
            std::cout << "BETA SAVE failed: " << err << "\n";
            return;
        }

        std::cout << "BETA SAVE: wrote " << foxref::beta_default_status_path() << "\n";
        return;
    }

    if (sub == "LOAD") {
        std::string err;
        if (!foxref::beta_load_overrides(&err)) {
            std::cout << "BETA LOAD failed: " << err << "\n";
            return;
        }

        std::cout << "BETA LOAD: read " << foxref::beta_default_status_path() << "\n";
        return;
    }

    print_usage();
}