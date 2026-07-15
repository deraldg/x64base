// ============================================================================
// File: src/help/helpdata_source_miner.hpp
// Purpose: Heuristic source-code mining for HELP DATA v2 candidate artifacts.
// ============================================================================
#pragma once

#include "helpdata_model.hpp"

#include <cstddef>
#include <string>
#include <vector>

namespace dottalk::helpdata {

struct SourceMineOptions {
    std::string default_catalog { "DOT" };

    bool mine_command_identity { true };
    bool mine_arguments { true };
    bool mine_syntax_strings { true };
    bool mine_message_strings { true };
    bool mine_message_symbols { true };

    // Safety guard for accidental scans of large generated files.
    std::size_t max_file_bytes { 2u * 1024u * 1024u };
};

struct SourceMineCounts {
    int files_seen { 0 };
    int files_scanned { 0 };
    int files_skipped { 0 };
    int command_contexts { 0 };
    int command_identity_facts { 0 };
    int argument_candidates { 0 };
    int syntax_candidates { 0 };
    int message_candidates { 0 };
    int message_symbol_candidates { 0 };
    int artifacts { 0 };
};

struct SourceMineResult {
    std::vector<Artifact> artifacts;
    SourceMineCounts counts;
};

// Recursively mines C/C++ source files under roots and returns normalized
// candidate artifacts. These are evidence rows, not authoritative docs.
// Throws std::runtime_error only for invalid root traversal errors that cannot
// be skipped by std::filesystem error_code-based iteration.
SourceMineResult mine_source_roots(const std::vector<std::string>& roots,
                                   const SourceMineOptions& options = {});

std::vector<Artifact> mine_source_artifacts(const std::vector<std::string>& roots,
                                            const SourceMineOptions& options = {});

} // namespace dottalk::helpdata
