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

    // Dev / transitional
    add("FILTER",    "SET FILTER",    "conditional_routed", "cmd_SETFILTER",      "core",      false, {"SET FILTER TO <expr>"});
    add("RELATION",  "SET RELATION",  "conditional_routed", "cmd_SET_RELATION",   "workspace", false, {"SET RELATION <args...>"});
    add("RELATIONS", "SET RELATIONS", "conditional_routed", "cmd_SET_RELATIONS",  "workspace", false, {"SET RELATIONS <args...>"});
    add("CNX",       "SET CNX",       "conditional_routed", "cmd_SETCNX",         "index",     false, {"SET CNX [TO] <container.cnx>"});
    add("CDX",       "SET CDX",       "conditional_routed", "cmd_SETCDX",         "index",     false, {"SET CDX [TO] <container.cdx>"});
    add("LMDB",      "SET LMDB",      "conditional_routed", "cmd_SETLMDB",        "index",     false, {"SET LMDB <args...>"});

    return out;
}

// ------------------------------------------------------------
// ENTRY VARIANTS
// ------------------------------------------------------------

std::vector<EntryVariantInfo> collect_entry_variants()
{
    std::vector<EntryVariantInfo> out;

    out.push_back({"SL", "SMARTLIST", "shortcut", "shortcut_resolver.hpp", ""});

    // DDL is canonical now; SCHEMA is compatibility alias.
    out.push_back({"SCHEMA", "DDL", "alias", "shell_commands.cpp", ""});

    out.push_back({"SETPATH", "SET PATH", "reexpression", "cmd_set.cpp", ""});
    out.push_back({"SET PATH TO", "SET PATH", "reexpression", "cmd_set.cpp", ""});

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
                   std::vector<std::string> syntax = {}) {
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
        cmd.syntax = std::move(syntax);

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

    add("DDL",
        "schema",
        "cmd_SCHEMA",
        "shell_commands.cpp",
        false,
        true,
        false,
        {"DDL <subcommand> ..."});
    add("SET",
        "core",
        "cmd_SET",
        "shell_commands.cpp",
        false,
        true,
        false,
        {"SET <option> [args]"});
    add("SMARTLIST",
        "core",
        "cmd_SMARTLIST",
        "shell_commands.cpp",
        false,
        false,
        false,
        {"SMARTLIST [options]..."});

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