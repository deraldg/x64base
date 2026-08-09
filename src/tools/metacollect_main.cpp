// @dottalk.file v1
// subsystem: tools
// layer: helper
// owns:
// project: project.x64base.runtime
// lane:
// owner: member.derald
// status: supported

// @dottalk.external v1
// owner: member.derald
// tool: metacollect
// external-kind: standalone-tool
// os-sensitive: no (portable C++ file I/O; builds and runs on any supported toolchain)
// target: the metacollect binary from src/tools/metacollect_main.cpp + src/meta/metacollect.cpp
// invocation: run the built exe directly with CLI flags; no launcher and not via datarun.ps1
// touches: reads the --source-root trees; writes metafacts to stdout and candidate CSVs to given paths
// requires: an isolated Release build with -DDOTTALK_BUILD_METACOLLECT=ON
// guard: read-only reflection; emits candidates only; never mutates metadata/help/runtime/source
// egress: none (local file I/O only)
// audit: candidate CSVs land under the run metacollect_phase/; a Gate 5 record binds them
// reversible: yes (candidate-only; delete the emitted CSVs to undo)
// notes:
//   metacollect is a standalone external developer tool, not a registered command and not
//   invoked by the engine. Outputs are review candidates; importing them into live metadata
//   is a separate reviewed gate. Runbook:
//   docs/maintenance/lanes/full_stack_documentation/METACOLLECT_RUNBOOK_V1.md.
//   Concept: labtalk/ai_portal/EXTERNAL_CALL_CONTRACT_V1.md.
// @dottalk.end

// ============================================================================
// File: src/tools/metacollect_main.cpp
// Purpose: Standalone developer entrypoint for read-only metadata extraction.
// Boundary: Emits reports only; never mutates metadata/help/runtime artifacts.
// ============================================================================

#include "dt/meta/metacollect.hpp"

#include <exception>
#include <fstream>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
    try {
        dt::meta::CollectOptions options;
        bool compare = false;
        bool workspace_root_set = false;
        std::string compare_out_path;
        std::string syscmd_import_out_path;
        std::string sysfunc_import_out_path;
        std::string sysargs_import_out_path;

        options.workspace_root = ".";

        for (int i = 1; i < argc; ++i) {
            const std::string arg = argv[i] ? argv[i] : "";

            if (arg == "--with-metadata") {
                options.include_metadata_tables = true;
            } else if (arg == "--compare") {
                compare = true;
                options.include_metadata_tables = true;
            } else if (arg == "--no-source") {
                options.include_source_catalogs = false;
            } else if (arg == "--no-skeleton-marker") {
                options.include_skeleton_marker = false;
            } else if (arg == "--sysargs-include-keywords") {
                options.include_usage_keyword_args = true;
            } else if (arg == "--include-dev-commands") {
                options.include_dev_command_contracts = true;
            } else if (arg == "--metadata-root" && i + 1 < argc) {
                options.metadata_dbf_root = argv[++i] ? argv[i] : "";
            } else if (arg == "--compare-out" && i + 1 < argc) {
                compare_out_path = argv[++i] ? argv[i] : "";
            } else if (arg == "--syscmd-import-out" && i + 1 < argc) {
                syscmd_import_out_path = argv[++i] ? argv[i] : "";
            } else if (arg == "--sysfunc-import-out" && i + 1 < argc) {
                sysfunc_import_out_path = argv[++i] ? argv[i] : "";
            } else if (arg == "--sysargs-import-out" && i + 1 < argc) {
                sysargs_import_out_path = argv[++i] ? argv[i] : "";
            } else if (arg == "--source-root" && i + 1 < argc) {
                options.source_roots.emplace_back(argv[++i] ? argv[i] : "");
            } else if (arg == "--source-ext" && i + 1 < argc) {
                options.source_extensions.emplace_back(argv[++i] ? argv[i] : "");
            } else if (!arg.empty() && arg[0] != '-' && !workspace_root_set) {
                options.workspace_root = arg;
                workspace_root_set = true;
            } else {
                std::cerr << "METACOLLECT error: unrecognized argument: " << arg << '\n';
                return 2;
            }
        }

        const auto result = dt::meta::collect_catalog_facts(options);

        for (const auto& warning : result.warnings) {
            std::cerr << "METACOLLECT warning: " << warning << '\n';
        }

        dt::meta::write_metafacts_csv(std::cout, result.facts);

        if (compare) {
            const auto issues = dt::meta::compare_catalog_facts(result.facts);
            std::cerr << "METACOLLECT compare: " << issues.size() << " issue(s)\n";

            if (!compare_out_path.empty()) {
                std::ofstream out(compare_out_path, std::ios::binary);
                if (!out) {
                    std::cerr << "METACOLLECT warning: cannot write compare report: "
                              << compare_out_path << '\n';
                } else {
                    dt::meta::write_compare_issues_csv(out, issues);
                }
            }
        }

        if (!syscmd_import_out_path.empty()) {
            std::ofstream out(syscmd_import_out_path, std::ios::binary);
            if (!out) {
                std::cerr << "METACOLLECT warning: cannot write SYSCMD import csv: "
                          << syscmd_import_out_path << '\n';
            } else {
                const auto rows = dt::meta::collect_syscmd_seed_rows(options);
                dt::meta::write_syscmd_seed_csv(out, rows);
                std::cerr << "METACOLLECT syscmd export: " << rows.size()
                          << " row(s)\n";
            }
        }

        if (!sysfunc_import_out_path.empty()) {
            std::ofstream out(sysfunc_import_out_path, std::ios::binary);
            if (!out) {
                std::cerr << "METACOLLECT warning: cannot write SYSFUNC import csv: "
                          << sysfunc_import_out_path << '\n';
            } else {
                const auto rows = dt::meta::collect_sysfunc_seed_rows();
                dt::meta::write_sysfunc_seed_csv(out, rows);
                std::cerr << "METACOLLECT sysfunc export: " << rows.size()
                          << " row(s)\n";
            }
        }

        if (!sysargs_import_out_path.empty()) {
            std::ofstream out(sysargs_import_out_path, std::ios::binary);
            if (!out) {
                std::cerr << "METACOLLECT warning: cannot write SYSARGS import csv: "
                          << sysargs_import_out_path << '\n';
            } else {
                const auto rows = dt::meta::collect_sysargs_seed_rows(options);
                dt::meta::write_sysargs_seed_csv(out, rows);
                std::cerr << "METACOLLECT sysargs export: " << rows.size()
                          << " row(s)\n";
            }
        }

        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "METACOLLECT error: " << ex.what() << '\n';
        return 2;
    }
}
