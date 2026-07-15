// src/cli/edu_missing_shims.cpp
// Temporary education-command shims for registry symbols that were declared
// in shell_commands.hpp but are not currently linked into this build.
//
// These shims are intentionally honest: they do not pretend to implement the
// full TEXT, EDIT, or COBOL subsystems. They keep the shell command registry
// linkable while the real educational modules are restored/refactored.
//
// Remove one shim at a time when a real implementation provides the same
// edu_* entrypoint.

// @dottalk.usage v1
// owner: EDU|MISSING_SHIMS
// command: TEXT/EDIT/COBOL shim aliases
// category: education-shim
// status: compatibility-shim
// noargs: report
// effect: report
// mutates: none
// usage-access: owned-by real TEXT/EDIT/COBOL implementations
// summary:
//   Fallback shim implementations used only when real EDU command
//   implementations are not linked.
//
// usage:
//   This file is not the canonical owner of TEXT, EDIT, or COBOL behavior.
//   User-visible usage belongs to the real command implementations:
//     edu_text.cpp
//     edu_edit.cpp
//     edu_cobol.cpp
//
// notes:
//   Remove shims one at a time when real implementations provide the same
//   symbols. Do not add new command behavior here unless deliberately creating
//   a fallback.
//
// risk:
//   mutates_table_data: no
//

#include "xbase.hpp"

#include <iostream>
#include <sstream>
#include <string>

using xbase::DbArea;

namespace {

void print_missing_edu_command(const char* name, const char* hint) {
    std::cout << name << ": educational command entrypoint is registered, "
              << "but the full implementation is not linked in this build.\n";
    if (hint && *hint) {
        std::cout << "  " << hint << "\n";
    }
}

} // namespace

void edu_TEXT(DbArea& /*A*/, std::istringstream& /*args*/) {
    print_missing_edu_command(
        "TEXT",
        "Restore the real TEXT implementation or change shell_commands.cpp to its existing handler."
    );
}

void edu_EDIT(DbArea& /*A*/, std::istringstream& /*args*/) {
    print_missing_edu_command(
        "EDIT",
        "Restore the real EDIT implementation or change shell_commands.cpp to its existing handler."
    );
}

void edu_COBOL(DbArea& /*A*/, std::istringstream& /*args*/) {
    print_missing_edu_command(
        "COBOL",
        "Restore the real COBOL implementation before relying on this educational command."
    );
}
