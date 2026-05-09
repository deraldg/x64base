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
