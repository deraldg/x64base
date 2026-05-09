// src/cli/cmd_foxhelp.cpp
// @dottalk.usage v1
// owner: DOT|FOXHELP
// command: FOXHELP
// category: help
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: FOXHELP USAGE
// summary:
//   List or search the static FoxPro-style command catalog.
//
// usage:
//   FOXHELP
//   FOXHELP USAGE
//   FOXHELP <name>
//   FOXHELP <search>
//   FH
//   FH <name>
//   FH <search>
//
// notes:
//   FOXHELP with no arguments lists the FoxPro-style command subset.
//   FOXHELP <name> prints an exact catalog item when found.
//   FOXHELP <search> searches the catalog and prints matching items.
//   FH is a short alias for FOXHELP.
//   FOXHELP is a read-only help/report command.
//
// risk:
//   reads_static_catalog: yes
//   mutates_table_data: no
//   mutates_session: no
//
// related:
//   HELP
//   CMDHELP
//   FOXSTANDARD
//

#include "xbase.hpp"
#include "textio.hpp"
#include "foxref.hpp"

#include <algorithm>
#include <cctype>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using xbase::DbArea;


static void print_foxhelp_usage() {
    std::cout
        << "Usage:\n"
        << "  FOXHELP\n"
        << "  FOXHELP USAGE\n"
        << "  FOXHELP <name>\n"
        << "  FOXHELP <search>\n"
        << "  FH\n"
        << "  FH <name>\n"
        << "  FH <search>\n"
        << "Notes:\n"
        << "  - FOXHELP with no arguments lists the FoxPro-style command subset.\n"
        << "  - FH is a short alias for FOXHELP.\n";
}

static bool is_foxhelp_usage_request(std::string raw) {
    std::string t = textio::up(textio::trim(std::move(raw)));
    if (t.rfind("FOXHELP ", 0) == 0) {
        t = textio::up(textio::trim(t.substr(8)));
    } else if (t.rfind("FH ", 0) == 0) {
        t = textio::up(textio::trim(t.substr(3)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_item(const foxref::Item& it) {
    std::cout << std::left << std::setw(14) << it.name
              << (it.supported ? " " : " (unsupported) ") << "\n";

    if (it.syntax && *it.syntax)
        std::cout << "  " << it.syntax << "\n";

    if (it.summary && *it.summary)
        std::cout << "  " << it.summary << "\n";
}

static void do_foxhelp(std::istringstream& in) {
    std::string rest;
    std::getline(in, rest);
    rest = textio::trim(rest);

    if (is_foxhelp_usage_request(rest)) {
        print_foxhelp_usage();
        return;
    }

    if (rest.empty()) {
        std::cout << "FoxPro-style commands (subset):\n";
        for (const auto& it : foxref::catalog()) {
            std::cout << "  " << std::left << std::setw(12) << it.name;
            if (it.supported) {
                std::cout << " - " << it.summary << "\n";
            } else {
                std::cout << " - " << it.summary << " [unsupported]\n";
            }
        }
        std::cout << "Tip: FOXHELP <NAME> for details, e.g. FOXHELP INDEX\n";
        return;
    }

    if (const auto* hit = foxref::find(rest); hit) {
        print_item(*hit);
        return;
    }

    auto results = foxref::search(rest);
    if (!results.empty()) {
        std::cout << "Matches for \"" << rest << "\":\n";
        for (const auto* it : results) {
            print_item(*it);
            std::cout << "\n";
        }
        return;
    }

    std::cout << "No help found for: " << rest << "\n";
    std::cout << "Try FOXHELP (no args) to list commands.\n";
}

void cmd_FOXHELP(DbArea& /*A*/, std::istringstream& in) {
    do_foxhelp(in);
}

void cmd_FH(DbArea& /*A*/, std::istringstream& in) {
    do_foxhelp(in);
}