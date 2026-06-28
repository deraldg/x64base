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
#include "cli/command_output.hpp"
#include "cli/output_router.hpp"

namespace {
std::ostream& out() {
    return cli::OutputRouter::instance().out();
}

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
    cli::cmdout::print_message(dottalk::helpdata::MessageId::DotHelpUsageText);
}

void print_item(const dotref::Item& it, bool verbose = true) {
    out() << it.name << "\n";
    out() << "  " << it.syntax << "\n";
    out() << "  " << it.summary << "\n";
    if (!it.supported) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::DotHelpUnsupportedNoteText);
    }
    if (verbose) out() << "\n";
}
} // namespace

void show_dot_help(const std::string& arg) {
    std::string term = to_upper(arg);
    if (term.empty()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::DotHelpTitleText);
        out() << "\n";
        cli::cmdout::print_message(dottalk::helpdata::MessageId::DotHelpSubtitleText);
        out() << "\n\n";
        for (const auto& item : dotref::catalog()) {
            out() << item.name << "\n"
                  << "  " << item.syntax << "\n"
                  << "  " << item.summary << "\n\n";
        }
        cli::cmdout::print_message(dottalk::helpdata::MessageId::DotHelpSearchUsageText);
        return;
    }
    if (const auto* item = dotref::find(term)) {
        print_item(*item, true);
        return;
    }
    auto matches = dotref::search(term);
    if (!matches.empty()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::DotHelpMatchesTitleText);
        out() << "\n";
        for (const auto* m : matches) {
            print_item(*m, false);
            out() << "\n";
        }
        return;
    }
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::DotHelpNoTopicText,
        {{"command", term}});
    cli::cmdout::print_message(dottalk::helpdata::MessageId::DotHelpTryHelpHintText);
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
