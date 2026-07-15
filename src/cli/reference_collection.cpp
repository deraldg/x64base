#include "help/reference_collection.hpp"

#include <algorithm>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

#include "cli/expr/function_catalog.hpp"
#include "cli/expr/fn_string.hpp"
#include "cli/expr/fn_date.hpp"
#include "cli/expr/fn_numeric.hpp"

namespace refsys {
namespace {

// ------------------------------------------------------------
// Helpers
// ------------------------------------------------------------

int narrow_size_to_int(std::size_t v, const char* field_name, const char* fn_name)
{
    if (v > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
        throw std::runtime_error(
            std::string("FunctionInfo overflow converting ") + field_name +
            " for function '" + fn_name + "'");
    }
    return static_cast<int>(v);
}

// ------------------------------------------------------------
// SET SUBCOMMANDS
// ------------------------------------------------------------

std::vector<SubcommandInfo> collect_set_subcommands()
{
    std::vector<SubcommandInfo> out;

    auto add = [&](const char* name,
                   const char* qualified_name,
                   const char* dispatch_style,
                   const char* handler_name,
                   const char* family,
                   const bool public_surface,
                   std::vector<std::string> syntax) {
        SubcommandInfo sc;
        sc.parent_command = "SET";
        sc.name = name;
        sc.qualified_name = qualified_name;
        sc.dispatch_style = dispatch_style;
        sc.handler_name = handler_name;
        sc.source_file = "cmd_set.cpp";
        sc.family = family;
        sc.authority = "command_catalog";
        sc.status = "partial";
        sc.implemented = true;
        sc.public_surface = public_surface;
        sc.uses_output_router = true;
        sc.uses_message_catalog = false;
        sc.syntax = std::move(syntax);
        out.push_back(std::move(sc));
    };

    // Public routed
    add("PATH",  "SET PATH",  "routed", "cmd_SETPATH",  "core",  true,
        {"SET PATH <slot> <path>"});
    add("INDEX", "SET INDEX", "routed", "cmd_SETINDEX", "index", true,
        {"SET INDEX TO <file>"});
    add("ORDER", "SET ORDER", "routed", "cmd_SETORDER", "index", true,
        {"SET ORDER TO <tag|0>"});

    // Public inline
    add("TALK",         "SET TALK",         "inline", "inline", "core",   true, {"SET TALK ON|OFF"});
    add("ECHO",         "SET ECHO",         "inline", "inline", "core",   true, {"SET ECHO ON|OFF"});
    add("PAGING",       "SET PAGING",       "inline", "inline", "core",   true, {"SET PAGING ON|OFF"});
    add("WRAP",         "SET WRAP",         "inline", "inline", "core",   true, {"SET WRAP ON|OFF"});
    add("DELETED",      "SET DELETED",      "inline", "inline", "core",   true, {"SET DELETED ON|OFF"});
    add("ALTERNATE",    "SET ALTERNATE",    "inline", "inline", "core",   true, {"SET ALTERNATE ON|OFF", "SET ALTERNATE TO <file>"});
    add("DEVICE",       "SET DEVICE",       "inline", "inline", "core",   true, {"SET DEVICE TO SCREEN|FILE <path>|PRINTER [name]|NULL"});
    add("PRINT",        "SET PRINT",        "inline", "inline", "core",   true, {"SET PRINT ON|OFF", "SET PRINT TO <file>"});
    add("EDITOR",       "SET EDITOR",       "inline", "inline", "core",   true, {"SET EDITOR TO <value|DEFAULT|OFF>"});
    add("TIMER",        "SET TIMER",        "inline", "inline", "core",   true, {"SET TIMER ON|OFF"});
    add("POLLING",      "SET POLLING",      "inline", "inline", "core",   true, {"SET POLLING ON|OFF"});
    add("TABLE BUFFER", "SET TABLE BUFFER", "inline", "inline", "buffer", true, {"SET TABLE BUFFER ON|OFF [ALL]"});

    // Public routed / conditional surfaces
    add("FILTER",    "SET FILTER",    "conditional_routed", "cmd_SETFILTER",      "core",      true, {"SET FILTER TO <expr>"});
    add("CASE",      "SET CASE",      "conditional_routed", "cmd_SETCASE",       "core",      true, {"SET CASE [ON|OFF]"});
    add("RELATION",  "SET RELATION",  "conditional_routed", "cmd_SET_RELATION",   "workspace", true, {"SET RELATION <args...>"});
    add("RELATIONS", "SET RELATIONS", "conditional_routed", "cmd_SET_RELATIONS",  "workspace", true, {"SET RELATIONS <args...>"});
    add("CNX",       "SET CNX",       "conditional_routed", "cmd_SETCNX",         "index",     true, {"SET CNX [TO] <container.cnx>"});
    add("CDX",       "SET CDX",       "conditional_routed", "cmd_SETCDX",         "index",     true, {"SET CDX [TO] <container.cdx>"});
    add("LMDB",      "SET LMDB",      "conditional_routed", "cmd_SETLMDB",        "index",     true, {"SET LMDB <args...>"});

    return out;
}

// ------------------------------------------------------------
// ENTRY VARIANTS
// ------------------------------------------------------------

std::vector<EntryVariantInfo> collect_entry_variants()
{
    std::vector<EntryVariantInfo> out;

    auto add = [&](const char* token,
                   const char* canonical_command,
                   const char* kind,
                   const char* source_file,
                   const char* notes = "") {
        out.push_back({token, canonical_command, kind, source_file, notes});
    };

    // Benign navigation / inspection aliases and shortcuts.
    add("GOTO", "GO", "alias", "shell_commands.cpp", "legacy navigation spelling");
    add("FIRST", "TOP", "alias", "shell_commands.cpp", "first-record navigation alias");
    add("LAST", "BOTTOM", "alias", "shell_commands.cpp", "last-record navigation alias");
    add("NEXT", "SKIP", "alias", "shell_commands.cpp", "relative navigation alias");
    add("PRIOR", "SKIP", "alias", "shell_commands.cpp", "relative navigation alias");
    add("SL", "SMARTLIST", "shortcut", "shortcut_resolver.hpp", "short list shortcut");

    // Index seek compatibility spellings.
    add("FIND", "SEEK", "alias", "cmd_seek.cpp", "FoxPro-style seek spelling");
    add("INDEXSEEK", "SEEK", "alias", "cmd_seek.cpp", "DotTalk++ index seek spelling");

    // DDL is canonical now; SCHEMA is compatibility alias.
    add("SCHEMA", "DDL", "alias", "shell_commands.cpp", "compatibility alias for DDL");

    // SET routed/reexpressed surfaces.
    add("SETPATH", "SET PATH", "reexpression", "cmd_set.cpp", "standalone compatibility form");
    add("SET PATH TO", "SET PATH", "reexpression", "cmd_set.cpp", "FoxPro-style path wording");
    add("SETINDEX", "SET INDEX", "reexpression", "cmd_set.cpp", "standalone compatibility form");
    add("SETORDER", "SET ORDER", "reexpression", "cmd_set.cpp", "standalone compatibility form");
    add("SETFILTER", "SET FILTER", "reexpression", "cmd_set.cpp", "standalone compatibility form");
    add("SETCASE", "SET CASE", "reexpression", "cmd_set.cpp", "standalone compatibility form");
    add("SETCNX", "SET CNX", "reexpression", "cmd_set.cpp", "developer/transitional standalone form");
    add("SETCDX", "SET CDX", "reexpression", "cmd_set.cpp", "developer/transitional standalone form");
    add("SETLMDB", "SET LMDB", "reexpression", "cmd_set.cpp", "developer/transitional standalone form");

    // Relationship compatibility spellings.
    add("RELATION", "REL", "alias", "cmd_rel.cpp", "singular relation topic alias");
    add("RELATIONS", "REL", "alias", "cmd_rel.cpp", "plural relation topic alias");
    add("CMDREL", "REL", "alias", "cmd_rel.cpp", "developer relation help alias");

    // Workspace compatibility spellings.
    add("SCHEMAS", "WORKSPACE", "alias", "cmd_workspace.cpp", "deprecated compatibility shim");

    return out;
}

// ------------------------------------------------------------
// FUNCTIONS (docs + runtime specs merged safely)
// ------------------------------------------------------------

std::vector<FunctionInfo> collect_functions()
{
    std::unordered_map<std::string, FunctionInfo> by_name;

    // 1. Seed from documented function catalog
    const auto docs = dottalk::expr::all_function_docs();
    for (const auto* doc : docs) {
        if (!doc) continue;

        FunctionInfo fn;
        fn.canonical_name = doc->name;
        fn.aliases = doc->aliases;
        fn.handler_name = "";
        fn.source_file = "function_catalog";
        fn.category = dottalk::expr::to_string(doc->category);
        fn.authority = "function_catalog";
        fn.status = "partial";
        fn.min_args = narrow_size_to_int(doc->min_args, "min_args", doc->name.c_str());
        fn.max_args = narrow_size_to_int(doc->max_args, "max_args", doc->name.c_str());
        fn.implemented = true;
        fn.public_surface = true;
        fn.callable_from_calc = true;
        fn.uses_message_catalog = false;

        fn.summary = doc->summary;
        fn.syntax = doc->syntax;
        fn.examples = doc->examples;
        fn.notes = doc->notes;
        fn.warnings = doc->warnings;

        by_name[fn.canonical_name] = std::move(fn);
    }

    // 2. Overlay/append runtime specs
    auto add_specs = [&](const dottalk::expr::BuiltinFnSpec* specs,
                         std::size_t count,
                         const char* category,
                         const char* source_file)
    {
        if (!specs) return;

        for (std::size_t i = 0; i < count; ++i) {
            const auto& spec = specs[i];
            std::string name = spec.name ? spec.name : "";
            if (name.empty()) continue;

            auto it = by_name.find(name);
            if (it == by_name.end()) {
                FunctionInfo fn;
                fn.canonical_name = name;
                fn.handler_name = "";
                fn.source_file = source_file;
                fn.category = category;
                fn.authority = "function_catalog";
                fn.status = "partial";
                fn.min_args = spec.minArgs;
                fn.max_args = spec.maxArgs;
                fn.implemented = true;
                fn.public_surface = true;
                fn.callable_from_calc = true;
                fn.uses_message_catalog = false;
                by_name.emplace(name, std::move(fn));
            } else {
                // keep doc richness, but make sure runtime truth wins where needed
                it->second.source_file = source_file;
                if (it->second.category.empty()) {
                    it->second.category = category;
                }
                it->second.min_args = spec.minArgs;
                it->second.max_args = spec.maxArgs;
            }
        }
    };

    add_specs(dottalk::expr::string_fn_specs(),
              dottalk::expr::string_fn_specs_count(),
              "string",
              "fn_string.cpp");

    add_specs(dottalk::expr::date_fn_specs(),
              dottalk::expr::date_fn_specs_count(),
              "date",
              "fn_date.cpp");

    add_specs(dottalk::expr::numeric_fn_specs(),
              dottalk::expr::numeric_fn_specs_count(),
              "numeric",
              "fn_numeric.cpp");

    std::vector<FunctionInfo> out;
    out.reserve(by_name.size());
    for (auto& kv : by_name) {
        out.push_back(std::move(kv.second));
    }

    std::sort(out.begin(), out.end(),
        [](const FunctionInfo& a, const FunctionInfo& b) {
            return a.canonical_name < b.canonical_name;
        });

    return out;
}

// ------------------------------------------------------------
// COMMANDS
// ------------------------------------------------------------

std::vector<CommandInfo> collect_commands(const ReferenceCollection& partial)
{
    std::vector<CommandInfo> out;

    auto add = [&](const char* canonical_name,
                   const char* family,
                   const char* handler_name,
                   const char* source_file,
                   const bool writes_console_direct,
                   const bool uses_output_router,
                   const bool uses_message_catalog,
                   std::vector<std::string> syntax = {},
                   const char* summary = "",
                   std::vector<std::string> examples = {},
                   std::vector<std::string> notes = {},
                   std::vector<std::string> warnings = {}) {
        CommandInfo cmd;
        cmd.canonical_name = canonical_name;
        cmd.family = family;
        cmd.authority = "command_catalog";
        cmd.status = "partial";
        cmd.handler_name = handler_name;
        cmd.source_file = source_file;
        cmd.implemented = true;
        cmd.public_surface = true;
        cmd.writes_console_direct = writes_console_direct;
        cmd.uses_output_router = uses_output_router;
        cmd.uses_message_catalog = uses_message_catalog;
        cmd.summary = summary ? summary : "";
        cmd.syntax = std::move(syntax);
        cmd.examples = std::move(examples);
        cmd.notes = std::move(notes);
        cmd.warnings = std::move(warnings);

        for (const auto& ev : partial.entry_variants) {
            if (ev.canonical_command != cmd.canonical_name) {
                continue;
            }
            if (ev.kind == "alias") {
                cmd.aliases.push_back(ev.token);
            } else if (ev.kind == "shortcut") {
                cmd.shortcuts.push_back(ev.token);
            } else if (ev.kind == "reexpression") {
                cmd.reexpressions.push_back(ev.token);
            }
        }

        out.push_back(std::move(cmd));
    };

    // Benign / low-risk usage coverage.
    add("HELP", "help", "cmd_HELP", "cmd_help.cpp", false, true, false,
        {"HELP", "HELP <command>", "HELP FUNCTION <name>", "HELP /FOX <topic>", "HELP /DOT <topic>", "HELP /ED <topic>"},
        "Show command, function, predicate, SQL, and system help topics",
        {"HELP", "HELP COUNT", "HELP FUNCTION ALLTRIM"},
        {"Default lookup checks reflected metadata before legacy refs"});

    add("GO", "navigation", "cmd_GO", "cmd_go.cpp", true, false, false,
        {"GO", "GO TOP", "GO BOTTOM", "GO [TO] <recno>", "GO RECORD <recno>", "GO +<n>", "GO -<n>"},
        "Move to a record or navigation endpoint",
        {"GO TOP", "GO TO 10", "GO -1"},
        {"Successful navigation intentionally moves the current record pointer"},
        {"IN <alias> is not supported yet"});

    add("TOP", "navigation", "cmd_TOP", "cmd_top.cpp", true, false, false,
        {"TOP"},
        "Move the current work-area cursor to the first logical record",
        {"TOP"},
        {"Uses active order when an order is active"});

    add("BOTTOM", "navigation", "cmd_BOTTOM", "cmd_bottom.cpp", true, false, false,
        {"BOTTOM"},
        "Move the current work-area cursor to the last logical record",
        {"BOTTOM"},
        {"Uses active order when an order is active"});

    add("SKIP", "navigation", "cmd_SKIP", "cmd_skip.cpp", true, false, false,
        {"SKIP", "SKIP <n>", "SKIP +<n>", "SKIP -<n>"},
        "Move the current work-area cursor forward or backward",
        {"SKIP", "SKIP 5", "SKIP -1"},
        {"Default movement is one record forward"});

    add("RECNO", "inspection", "cmd_RECNO", "cmd_recno.cpp", true, false, false,
        {"RECNO", "RECNO()"},
        "Show or return the current record number",
        {"RECNO", "? RECNO()"},
        {"Command form prints the current record number"});

    add("AREA", "inspection", "cmd_AREA", "shell_commands.cpp", true, false, false,
        {"AREA"},
        "Report the current work-area slot and table context",
        {"AREA"},
        {"Non-mutating inspection command"});

    add("DBAREAS", "inspection", "cmd_DBAREAS", "cmd_dbareas.cpp", true, false, false,
        {"DBAREAS"},
        "Report all open DbArea/workspace slots",
        {"DBAREAS"},
        {"Useful after WORKSPACE LOAD or setup scripts"});

    add("COUNT", "inspection", "cmd_COUNT", "cmd_count.cpp", true, false, false,
        {"COUNT", "COUNT ALL", "COUNT DELETED", "COUNT NOT DELETED", "COUNT FOR <expr>", "COUNT WHERE <expr>"},
        "Count records in the current work area",
        {"COUNT", "COUNT FOR LNAME = \"SMITH\""},
        {"Preserves the current record position", "Uses current SET FILTER if active"});

    add("DISPLAY", "inspection", "cmd_DISPLAY", "cmd_display.cpp", true, false, false,
        {"DISPLAY", "DISPLAY <recno>", "DISPLAY FIELDS <fieldlist>"},
        "Display field values for the current or specified record",
        {"DISPLAY", "DISPLAY 10"},
        {"Displays all fields for the current record by default"});

    add("STATUS", "inspection", "cmd_STATUS", "cmd_status.cpp", true, false, false,
        {"STATUS"},
        "Display current table/work-area status",
        {"STATUS"},
        {"Non-mutating status checkpoint command"});

    add("STRUCT", "inspection", "cmd_STRUCT", "cmd_struct.cpp", true, false, false,
        {"STRUCT"},
        "Display the structure of the current table",
        {"STRUCT"},
        {"Non-mutating structure inspection command"});

    add("FIELDS", "inspection", "cmd_FIELDS", "cmd_fields.cpp", true, false, false,
        {"FIELDS"},
        "List fields for the current table",
        {"FIELDS"},
        {"Compact field-list view; use STRUCT for fuller structure output"});

    add("VERSION", "inspection", "cmd_VERSION", "cmd_version.cpp", true, false, false,
        {"VERSION"},
        "Print build and version information",
        {"VERSION"},
        {"Useful at the top of regression logs and shakedown transcripts"});

    add("REFRESH", "inspection", "cmd_REFRESH", "cmd_refresh.cpp", true, false, false,
        {"REFRESH"},
        "Refresh internal state or the active view where supported",
        {"REFRESH"},
        {"Specific behavior depends on the active subsystem"});

    add("COLOR", "presentation", "cmd_COLOR", "cmd_color.cpp", true, false, false,
        {"COLOR", "COLOR GREEN", "COLOR AMBER", "COLOR DEFAULT", "COLOR G+"},
        "Switch CLI/TUI color theme",
        {"COLOR GREEN", "COLOR DEFAULT"},
        {"Presentation-only command"});

    // First controlled advanced-command usage pass.
    add("DDL", "schema", "cmd_SCHEMA", "shell_commands.cpp", false, true, false,
        {"DDL <subcommand> ..."},
        "Canonical schema/definition command family",
        {},
        {"SCHEMA is a compatibility alias; WORKSPACE owns live session state"});

    add("SET", "core", "cmd_SET", "shell_commands.cpp", false, true, false,
        {"SET <option> [args]", "SET INDEX TO <table>.cdx", "SET ORDER TO TAG <tag> [IN <alias>]", "SET FILTER TO <expr>", "SET PATH <slot> <path>"},
        "Route modern SET options such as index, order, filter, relation, and output settings",
        {"SET INDEX TO students.cdx", "SET ORDER TO TAG lname", "SET FILTER TO GPA >= 3.5"},
        {"SET is the public router; standalone SET* commands are compatibility targets", "SET INDEX names the logical CDX container, not the physical LMDB backend"});

    add("SMARTLIST", "listing", "cmd_SMARTLIST", "shell_commands.cpp", false, false, false,
        {"SMARTLIST", "SMARTLIST <n>", "SMARTLIST ALL", "SMARTLIST DELETED", "SMARTLIST FOR <expr>", "SMARTLIST DEBUG"},
        "Order-aware list output with predicate support",
        {"SMARTLIST", "SMARTLIST 20", "SMARTLIST FOR LNAME LIKE \"SMI%\""},
        {"Preferred listing command for user-facing ordered output"});

    add("LIST", "listing", "cmd_LIST", "cmd_list.cpp", true, false, false,
        {"LIST", "LIST ALL", "LIST DELETED", "LIST FIELDS <fieldlist>", "LIST FOR <expr>", "LIST NEXT <n>", "LIST REST"},
        "List records from the current work area",
        {"LIST", "LIST FIELDS LNAME,FNAME", "LIST FOR GPA >= 3.5"},
        {"Developer inspection command; SMARTLIST is preferred for order-aware listing"});

    add("SEEK", "index", "cmd_SEEK", "cmd_seek.cpp", true, false, false,
        {"SEEK <expr>", "SEEK <expr> IN <alias>"},
        "Seek an exact value using the active index/order",
        {"SEEK \"SMITH\"", "SEEK 1001"},
        {"Successful SEEK intentionally moves the current record pointer", "Public wording should remain at CDX/tag/order level"},
        {"Do not document direct LMDB path parsing as public SEEK behavior"});

    add("REL", "relation", "cmd_REL", "cmd_rel.cpp", true, false, false,
        {"REL LIST", "REL LIST ALL", "REL REFRESH", "REL ADD <parent> <child> ON <field>", "REL ADD <parent> <child> ON <parentField> TO <childField>", "REL CLEAR <parent>|ALL", "REL ENUM [LIMIT <n>] <path...> TUPLE <projection>"},
        "Manage and inspect the DotTalk++ relation graph",
        {"REL LIST", "REL ADD STUDENTS ENROLL ON SID", "REL REFRESH"},
        {"REL is the native relation backend", "FoxPro-style SET RELATION syntax routes into this model where implemented"});

    add("WORKSPACE", "workspace", "cmd_WORKSPACE", "cmd_workspace.cpp", true, false, false,
        {"WORKSPACE", "WORKSPACE OPEN DBF", "WORKSPACE OPEN <dir>", "WORKSPACE CLOSE", "WORKSPACE SAVE <name>", "WORKSPACE LOAD <name>"},
        "Manage live work-area/session state",
        {"WORKSPACE", "WORKSPACE CLOSE", "WORKSPACE LOAD mcc.dtschemas"},
        {"WORKSPACE owns live areas, aliases, orders, and relation/session layout", "DDL owns schema/definition work"});

    add("COMMIT", "mutation", "cmd_COMMIT", "table_buffer.cpp", true, false, false,
        {"COMMIT", "COMMIT ALL"},
        "Apply staged table-buffered changes",
        {"COMMIT"},
        {"Mutation boundary; keep help wording conservative until runtime behavior is verified", "Index maintenance should flow through the index subsystem"});

    std::sort(out.begin(), out.end(),
        [](const CommandInfo& a, const CommandInfo& b) {
            return a.canonical_name < b.canonical_name;
        });

    return out;
}

} // anonymous namespace

ReferenceCollection build_reference_collection()
{
    ReferenceCollection rc;

    rc.subcommands = collect_set_subcommands();
    rc.entry_variants = collect_entry_variants();
    rc.functions = collect_functions();
    rc.commands = collect_commands(rc);

    rc.args = {};
    rc.messages = {};

    return rc;
}

} // namespace refsys
