// @dottalk.usage v1
// owner: DOT|SETPATH_PATHS_IMPL
// command: SETPATH
// category: environment-helper
// status: implementation-helper
// noargs: n/a
// effect: path-slot-support
// mutates: path-slots-through-api
// usage-access: owned-by cmd_setpath_command.cpp
// summary:
//   Path-slot support implementation used by SETPATH and related commands.
//
// usage:
//   This file does not export cmd_SETPATH.
//   Runtime SETPATH usage is owned by the command handler in cmd_setpath_command.cpp.
//
// notes:
//   This file owns path-slot normalization, defaults, and dump/report support.
//   Do not add shell dispatch here unless SETPATH ownership is moved deliberately.
//
// risk:
//   mutates_path_slots: through dottalk::paths API calls
//   mutates_table_data: no
//

#include "cli/cmd_setpath.hpp"

#include <filesystem>
#include <sstream>

namespace dottalk::paths {

namespace {

fs::path norm_abs(const fs::path& p)
{
    try {
        return std::filesystem::absolute(p).lexically_normal();
    } catch (...) {
        return p;
    }
}

} // namespace

void set_slot_from_value(Slot slot, const fs::path& value)
{
    set_slot(slot, norm_abs(value));
}

void init_defaults(const fs::path& data_root)
{
    const fs::path root = norm_abs(data_root);
    const fs::path appRoot = root.parent_path();

    set_slot(Slot::DATA,            root);
    set_slot(Slot::DOCS,            appRoot / "docs");
    set_slot(Slot::SYSTEM_DIAGRAMS, appRoot / "docs" / "generated" / "diagrams");
    set_slot(Slot::USER_DIAGRAMS,   appRoot / "user" / current_user() / "diagrams");
    set_slot(Slot::DBF,             root / "dbf");
    set_slot(Slot::XDBF,       root / "xdbf");
    set_slot(Slot::INDEXES,    root / "indexes");
    set_slot(Slot::LMDB,       root / "lmdb");
    set_slot(Slot::WORKSPACES, root / "workspaces");
    set_slot(Slot::SCHEMAS,    root / "schemas");
    set_slot(Slot::PROJECTS,   root / "projects");
    set_slot(Slot::SCRIPTS,    root / "scripts");
    set_slot(Slot::TESTS,      root / "tests");
    set_slot(Slot::HELP,       root / "help");
    set_slot(Slot::LOGS,       root / "logs");
    set_slot(Slot::TMP,        root / "tmp");
}

std::string dump()
{
    std::ostringstream os;

    os << "SETPATH\n";
    os << "----------------------------------------\n";
    os << "  DATA            = " << get_slot(Slot::DATA).string() << "\n";
    os << "  DOCS            = " << get_slot(Slot::DOCS).string() << "\n";
    os << "  SYSTEM_DIAGRAMS = " << get_slot(Slot::SYSTEM_DIAGRAMS).string() << "\n";
    os << "  USER_DIAGRAMS   = " << get_slot(Slot::USER_DIAGRAMS).string() << "\n";
    os << "  DBF             = " << get_slot(Slot::DBF).string() << "\n";
    os << "  XDBF            = " << get_slot(Slot::XDBF).string() << "\n";
    os << "  INDEXES         = " << get_slot(Slot::INDEXES).string() << "\n";
    os << "  LMDB            = " << get_slot(Slot::LMDB).string() << "\n";
    os << "  WORKSPACES      = " << get_slot(Slot::WORKSPACES).string() << "\n";
    os << "  SCHEMAS         = " << get_slot(Slot::SCHEMAS).string() << "\n";
    os << "  PROJECTS        = " << get_slot(Slot::PROJECTS).string() << "\n";
    os << "  SCRIPTS         = " << get_slot(Slot::SCRIPTS).string() << "\n";
    os << "  TESTS           = " << get_slot(Slot::TESTS).string() << "\n";
    os << "  HELP            = " << get_slot(Slot::HELP).string() << "\n";
    os << "  LOGS            = " << get_slot(Slot::LOGS).string() << "\n";
    os << "  TMP             = " << get_slot(Slot::TMP).string() << "\n";

    return os.str();
}

} // namespace dottalk::paths
