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

constexpr std::array<RegressionSpec, 19> kRegressionSpecs{{
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
    },
    {
        "DOTSCRIPT_EXPR",
        "dotscript\\dotscript_expr_regression.dts",
        "DotScript memvars (VAR/$name) + arrays ({}/$a[n], nested/chained) via the house expression path, with an IF literal baseline (AIF-041 M1)",
        true
    },
    {
        "DOTSCRIPT_PARITY",
        "dotscript\\predicate_memvar_parity_regression.dts",
        "Predicate parity target: $name/$a[n] in IF/WHILE/WHERE — now GREEN via the shared house-evaluator bridge (AIF-041, landed 2026-07-21). Fixture-free, self-asserting; safe for the default suite",
        true
    },
    {
        "LEXING",
        "lexing\\comment_handling_regression.dts",
        "Canonical comment vocabulary on the script path after the AIF-037 lexer consolidation (full-line * REM # //, inline && #, single & macro survives); read-only, fixture-free",
        true
    },
    {
        "CALC",
        "calc\\calc_output_regression.dts",
        "CALC output-routing regression: every ValueKind path (Bool/Number/String/Date/empty/Error) via cli::cmdout::print_line (AIF-031); read-only, but leaves ECHO ON so it stays out of the default suite (explicit run)",
        false
    },
    {
        "ERRORSTOP",
        "errorstop\\stop_on_error_regression.dts",
        "stop_on_error threshold: OFF continues past a recorded error, ERROR aborts at the failing line; self-contained, but Phase-2 aborts leaving STOP_ON_ERROR ON so it stays out of the default suite (explicit run) (AIF-036)",
        false
    },
    {
        "WAL_COMMIT_ROLLBACK",
        "pinocchio\\wal_commit_rollback_regression.dts",
        "WAL durability: COMMIT applies a buffered+logged REPLACE, ROLLBACK discards one; self-bootstrapping (creates+erases a throwaway WALREGR table, never touches the students fixture), self-asserting W0/W1/W2 markers. Mutates the filesystem so it stays out of the default suite (explicit run) (AIF-017/023)",
        false
    },
    // NOTE: this WAL_COMMIT_ROLLBACK entry replaces the legacy commit_rollback_test.dts,
    // which assumed an already-open `students` table, did not self-bootstrap (regression
    // doctrine violation), and silently no-op'd when run standalone. The self-contained
    // basis is pinocchio\wal_phaseA_proof.dts (throwaway table, ERASEd at end).
    {
        "INDEX_TXN",
        "migrated\\index_txn_lmdb_maintenance.dts",
        "SET INDEXTXN transactional in-COMMIT index maintenance: buffered REPLACE/DELETE + COMMIT maintains the live CDX/LMDB index with NO BUILDLMDB. Self-asserting and fixture-free (builds + erases its own throwaway x64 IDXTXN table; never touches students). Scored on ORDERED position = index-truth (T1 commit-maintains, T2 dup-survivor): OFF => .F. (RED), ON => .T. (GREEN). Mode is env-driven (DOTTALK_INDEX_TXN) or runtime SET INDEXTXN; the script does not force the flag. Out of the default suite (mutates the filesystem; explicit run) (AIF-027/023; feeds AIF-041 M1)",
        false
    },
    {
        "SCAN_PARITY",
        "dotscript\\scan_memvar_parity_regression.dts",
        "Scan-path parity: $name resolves in a FOR/scan predicate (eval_bool: LOCATE/COUNT/SCAN/LIST FOR + SET FILTER) via the shared bridge. GREEN since the AIF-041 scan convergence landed (2026-07-21). Self-bootstrapping throwaway SCANREGR in SANDBOX; stays out of the default suite because it mutates the filesystem (explicit run) (AIF-041)",
        false
    },
    {
        "DEF_FAMILY",
        "dotscript\\def_family_regression.dts",
        "Runtime DEF-family testbed: DEFCMD/DEFFN/EXAMPLE define-invoke-arg-compose-list-remove, session-only, no rebuild (RUNTIME_DEF_FAMILY lane). Self-bootstrapping; opens/mutates no table or file (only the session command/function registries, which it cleans up). Permanent worked example of the AI-friendly dev-tools. Explicit-run until proven green in-suite, then promote to default.",
        false
    },
    {
        "MEM",
        "mem_proof.dts",
        "AIF-043 in-memory indexed table end-to-end proof: DO mem mounts the in-process RAM VFS (xbase::ramfs), then an x64 table AND its native CDX-V64 index are built, indexed, and traversed entirely in RAM (RUN8, no LMDB, zero files on disk). Self-contained (leads with DO mem, clean-slate remount) and self-asserting: ordered read-back must yield ADAMS/MILLER/ZEBRA (MEM_T1/T2/T3 = .T.); teardown unmounts and restores the x64 disk env. Mutates the RAM VFS only (no disk table), but kept out of the default suite (explicit run) until soaked. (AIF-043)",
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
