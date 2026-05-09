// @dottalk.usage v1
// owner: DOT|DOTHELP
// command: DOTHELP
// category: help
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: DOTHELP USAGE
// summary:
//   Show project-native DotTalk++ reference entries from the dotref catalog.
//
// usage:
//   DOTHELP
//   DOTHELP USAGE
//   DOTHELP <term>
//   HELP /DOT <term>
//
// notes:
//   DOTHELP with no arguments lists project-native commands and subsystems.
//   DOTHELP <term> prints a matching dotref entry or search matches.
//   DOTHELP USAGE prints usage only.
//   HELP /DOT <term> is the related HELP-surface access path.
//   DOTHELP is read-only.
//
// risk:
//   mutates_table_data: no
//   mutates_session: no
//
// related:
//   HELP
//   FOXHELP
//   CMDHELP
//

#include "xbase.hpp"
#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include "dotref.hpp"

namespace {
std::string to_upper(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}


std::string dothelp_trim(std::string s) {
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

bool is_dothelp_usage_request(const std::string& raw) {
    std::string t = to_upper(dothelp_trim(raw));
    if (t.rfind("DOTHELP ", 0) == 0) {
        t = to_upper(dothelp_trim(t.substr(8)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

void print_dothelp_usage() {
    std::cout
        << "Usage:\n"
        << "  DOTHELP\n"
        << "  DOTHELP USAGE\n"
        << "  DOTHELP <term>\n"
        << "  HELP /DOT <term>\n";
}

void print_item(const dotref::Item& it, bool verbose = true) {
    std::cout << it.name << "\n";
    std::cout << "  " << it.syntax << "\n";
    std::cout << "  " << it.summary << "\n";
    if (!it.supported) {
        std::cout << "  (documented, but not fully supported yet)\n";
    }
    if (verbose) std::cout << "\n";
}
} // namespace

void show_dot_help(const std::string& arg) {
    std::string term = to_upper(arg);
    if (term.empty()) {
        std::cout << "DOTTALK REFERENCE\n\n"
                  << "Project-native commands and subsystems\n\n";
        for (const auto& item : dotref::catalog()) {
            std::cout << item.name << "\n"
                      << "  " << item.syntax << "\n"
                      << "  " << item.summary << "\n\n";
        }
        std::cout << "Usage:\n"
                  << "  DOTHELP <term>\n"
                  << "  HELP /DOT <term>\n";
        return;
    }
    if (const auto* item = dotref::find(term)) {
        print_item(*item, true);
        return;
    }
    auto matches = dotref::search(term);
    if (!matches.empty()) {
        std::cout << "Matching DotTalk helpers:\n\n";
        for (const auto* m : matches) {
            print_item(*m, false);
            std::cout << "\n";
        }
        return;
    }
    std::cout << "No DotTalk help found for: " << term << "\n"
              << "Try HELP /DOT <term> or plain HELP <term>.\n";
}

void cmd_DOTHELP(xbase::DbArea& /*area*/, std::istringstream& iss) {
    std::string args;
    std::getline(iss >> std::ws, args);
    if (is_dothelp_usage_request(args)) {
        print_dothelp_usage();
        return;
    }
    show_dot_help(args);
}
