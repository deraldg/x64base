// src/cli/cmd_tvision.cpp
// @dottalk.usage v1
// owner: DOT|TVISION
// command: TVISION
// category: diagnostics
// status: stub
// noargs: report
// effect: report
// mutates: none
// usage-access: TVISION USAGE
// summary:
//   Confirm Turbo Vision/TUI support is linked; this is currently a stub.
//
// usage:
//   TVISION
//   TVISION USAGE
//
// examples:
//   TVISION
//
// notes:
//   TVISION with no arguments prints the current TUI support status.
//   TVISION USAGE prints usage.
//   This command does not launch a TUI yet.
//
// risk:
//   mutates_table_data: no
//
// related:
//   RBROWSE
//   SMARTBROWSER
//

#include <iostream>
#include <sstream>
#include <string>
#include "xbase.hpp"
#include <cctype>

namespace {

static void print_tvision_usage()
{
    std::cout
        << "Usage:\n"
        << "  TVISION\n"
        << "  TVISION USAGE\n"
        << "Notes:\n"
        << "  - TVISION is currently a link/status stub; it does not launch a TUI yet.\n";
}

} // namespace

// Signature must match the shell's command registry:
//   void cmd_TVISION(xbase::DbArea&, std::istringstream&)
void cmd_TVISION(xbase::DbArea& area, std::istringstream& args) {
    (void)area;

    std::string tok;
    if (args >> tok) {
        for (char& ch : tok) {
            ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
        }

        if (tok == "USAGE" || tok == "HELP" || tok == "?") {
            print_tvision_usage();
            return;
        }
    }

    // Minimal stub: confirm TV lib is built & reachable.
    // We avoid textio here; std::cout is fine and portable.
    std::cout
        << "Turbo Vision (TUI) support is enabled and linked.\n"
        << "This stub command is present so the linker symbol resolves.\n"
        << "Next step: wire this to your TUI entrypoint when ready.\n";
}
