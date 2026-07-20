// src/cli/cmd_regression.cpp
// @dottalk.usage v1
// owner: DOT|REGRESSION
// command: REGRESSION
// category: test
// status: supported
// noargs: usage
// effect: execute
// mutates: delegates regression scripts session data filesystem
// usage-access: REGRESSION USAGE
// summary:
//   Launch curated DotTalk++ regression and smoke DotScript files through the
//   normal DOTSCRIPT runner so regression entrypoints stay discoverable and
//   consistent.
//
// usage:
//   REGRESSION USAGE
//   REGRESSION LIST
//   REGRESSION SHOW <name>
//   REGRESSION RUN <name>
//   REGRESSION <name>
//   REGRESSION ALL
//
// examples:
//   REGRESSION LIST
//   REGRESSION SHOW NONDESTRUCTIVE
//   REGRESSION RUN INDEX_X32
//   REGRESSION RUN X64_METRICS
//   REGRESSION RUN HARVEST
//   REGRESSION CURSOR
//   REGRESSION ALL
//
// notes:
//   REGRESSION is a curated launcher, not a separate test executor.
//   Actual script execution is delegated to DOTSCRIPT.
//   Regression scripts are expected to bootstrap their own environment.
//   LIST shows only curated stable entrypoints, not every historical script on disk.
//   ALL runs the curated default suite in declared order.
//   Dev-only warning/repro canaries should remain outside this surface unless
//   they are intentionally promoted.
//
// risk:
//   reads_files: yes
//   executes_commands: yes
//   mutates_data: depends on selected script contents
//   mutates_session: yes
//   writes_files: depends on selected script contents
//   no_transaction_or_rollback: yes
//
// related:
//   DOTSCRIPT
//   TEST
//   WORKSPACE
//   ERSATZ
//   CMDHELP
//

#include "shell_commands.hpp"

#include <array>
#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>

#include "common/path_state.hpp"
#include "shell_api.hpp"
#include "textio.hpp"

using xbase::DbArea;

namespace {

struct RegressionSpec {
    const char* name;
    const char* script;
    const char* summary;
    bool in_default_suite;
};

constexpr std::array<RegressionSpec, 9> kRegressionSpecs{{
    {
        "NONDESTRUCTIVE",
        "dottalkpp_non_destructive_smoke.dts",
        "Broad non-destructive shell smoke over stable command surface",
        true
    },
    {
        "INDEX_X32",
        "index_x32_inx_cnx_smoke.dts",
        "x32 INX/CNX order and attachment smoke",
        true
    },
    {
        "INDEX_X64",
        "index_v64_cdx_lmdb_smoke.dts",
        "v64 CDX/LMDB order and attachment smoke",
        true
    },
    {
        "X64_METRICS",
        "canaries\\x64_matrix_metrics_boundary_canary.dts",
        "x64 structural boundary proof above legacy 16-bit record/header limits",
        true
    },
    {
        "LANGUAGE",
        "canaries\\language_shakedown_canary.dts",
        "Messaging-normalization locale proof: es/fr/de/it USAGE render across the localized command surface",
        true
    },
    {
        "HARVEST",
        "main\\harvest_top_shakedown.dts",
        "Top-layer harvest proof across regression launcher, security roles, holiday demos, and curated runtime shakedowns",
        false
    },
    {
        "CURSOR",
        "CURSOR_FAMILY_REGRESSION_001.DTS",
        "Navigation/cursor family regression on classic ordered traversal",
        false
    },
    {
        "RELJOIN",
        "main\\rel_join_enum_regression.dts",
        "Relation join/enum projection regression",
        false
    },
    {
        "LIMITS",
        "limits\\limits_all_shakedown.dts",
        "Engine limit guardrails: MAX_AREA=512, x64 name ceilings 256, record-size advisory, CLOSE ALL over every open area",
        false
    }
}};

std::string trim_copy(std::string s)
{
    const auto is_ws = [](unsigned char c) { return std::isspace(c) != 0; };
    while (!s.empty() && is_ws(static_cast<unsigned char>(s.front()))) {
        s.erase(s.begin());
    }
    while (!s.empty() && is_ws(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

std::string upper_copy(std::string s)
{
    for (char& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

const RegressionSpec* find_regression_spec(const std::string& token)
{
    const std::string key = upper_copy(trim_copy(token));
    for (const auto& spec : kRegressionSpecs) {
        if (key == spec.name) return &spec;
    }
    return nullptr;
}

std::filesystem::path resolve_regression_script_path(const RegressionSpec& spec)
{
    namespace fs = std::filesystem;

    const fs::path raw(spec.script);
    if (raw.is_absolute()) return raw.lexically_normal();

    try {
        const fs::path scripts_root = dottalk::paths::get_slot(dottalk::paths::Slot::SCRIPTS);
        if (!scripts_root.empty()) {
            const fs::path rooted = (scripts_root / raw).lexically_normal();
            if (fs::exists(rooted) && fs::is_regular_file(rooted)) {
                return fs::weakly_canonical(rooted);
            }
            return rooted;
        }
    } catch (...) {
    }

    return shell_resolve_script_path(spec.script);
}

void print_regression_usage()
{
    std::cout
        << "Usage:\n"
        << "  REGRESSION USAGE\n"
        << "  REGRESSION LIST\n"
        << "  REGRESSION SHOW <name>\n"
        << "  REGRESSION RUN <name>\n"
        << "  REGRESSION <name>\n"
        << "  REGRESSION ALL\n"
        << "Notes:\n"
        << "  - REGRESSION is a curated launcher over DOTSCRIPT.\n"
        << "  - Scripts are expected to bootstrap their own environment.\n"
        << "  - LIST shows curated stable entrypoints rather than every historical script.\n"
        << "  - ALL runs the curated default suite in declared order.\n"
        << "  - HARVEST is the top-layer shakedown for newly promoted surfaces.\n"
        << "  - LANGUAGE proves es/fr/de/it USAGE rendering across the localized command surface.\n";
}

void print_regression_list()
{
    std::cout << "Curated regressions:\n";
    for (const auto& spec : kRegressionSpecs) {
        std::cout << "  " << spec.name;
        if (spec.in_default_suite) std::cout << "  [default]";
        std::cout << "\n"
                  << "    " << spec.summary << "\n"
                  << "    " << spec.script << "\n";
    }
}

void print_regression_show(const RegressionSpec& spec)
{
    const std::filesystem::path resolved = resolve_regression_script_path(spec);

    std::cout << "REGRESSION: " << spec.name << "\n"
              << "  Summary : " << spec.summary << "\n"
              << "  Script  : " << spec.script << "\n"
              << "  Resolved: " << resolved.string() << "\n"
              << "  Default : " << (spec.in_default_suite ? "yes" : "no") << "\n";
}

void run_regression_script(DbArea& area, const RegressionSpec& spec)
{
    const std::filesystem::path resolved = resolve_regression_script_path(spec);

    std::cout << "REGRESSION: running " << spec.name << "\n"
              << "  Script: " << spec.script << "\n"
              << "  Resolved: " << resolved.string() << "\n";

    std::ostringstream dotscript_line;
    dotscript_line << '"' << resolved.string() << '"';
    std::istringstream dotscript_args(dotscript_line.str());
    cmd_DOTSCRIPT(area, dotscript_args);
}

void run_regression_default_suite(DbArea& area)
{
    for (const auto& spec : kRegressionSpecs) {
        if (!spec.in_default_suite) continue;
        run_regression_script(area, spec);
    }
}

} // namespace

void cmd_REGRESSION(DbArea& area, std::istringstream& in)
{
    std::string arg1;
    if (!(in >> arg1)) {
        print_regression_usage();
        return;
    }

    const std::string op = upper_copy(arg1);

    if (op == "USAGE" || op == "HELP" || op == "?") {
        print_regression_usage();
        return;
    }

    if (op == "LIST") {
        print_regression_list();
        return;
    }

    if (op == "ALL") {
        run_regression_default_suite(area);
        return;
    }

    if (op == "SHOW" || op == "RUN") {
        std::string name;
        if (!(in >> name)) {
            std::cout << "REGRESSION: missing regression name.\n";
            print_regression_usage();
            return;
        }
        const RegressionSpec* spec = find_regression_spec(name);
        if (!spec) {
            std::cout << "REGRESSION: unknown regression '" << name << "'.\n";
            print_regression_list();
            return;
        }
        if (op == "SHOW") {
            print_regression_show(*spec);
        } else {
            run_regression_script(area, *spec);
        }
        return;
    }

    if (const RegressionSpec* spec = find_regression_spec(op)) {
        run_regression_script(area, *spec);
        return;
    }

    std::cout << "REGRESSION: unknown option or regression '" << arg1 << "'.\n";
    print_regression_list();
}
