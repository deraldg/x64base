// ============================================================================
// File: src/cli/helpdata_cmdhelp_bridge.hpp
// Purpose: CLI-side bridge from existing CMDHELP/command docs into HELP DATA v2.
// ============================================================================
#pragma once

#include <string>
#include <vector>

#include "cmdhelp.hpp"
#include "../help/helpdata_model.hpp"

namespace cmdhelp {

struct HelpDataV2Counts {
    int command_status_rows { 0 };
    int legacy_catalog_rows { 0 };
    int curated_doc_rows { 0 };
    int standard_message_rows { 0 };
    int mined_source_rows { 0 };
    int total_artifact_rows { 0 };
    int exported_artifact_rows { 0 };

    // Source miner diagnostics. These are for operator confidence and
    // CMDHELPCHK-style validation, not for user-facing command help.
    int source_files_seen { 0 };
    int source_files_scanned { 0 };
    int source_files_skipped { 0 };
    int source_command_contexts { 0 };
    int source_command_identity_facts { 0 };
    int source_argument_candidates { 0 };
    int source_syntax_candidates { 0 };
    int source_message_candidates { 0 };
    int source_message_symbol_candidates { 0 };
    int source_artifact_cap_hit { 0 }; // 1 when strict miner reached its current safety cap.

    // Direct @dottalk.usage v1 contract mining supplement. This exists so
    // command-owned usage contracts are authoritative even when the heuristic
    // source miner skips small/report/help/navigation files or hits a safety cap.
    int usage_contract_files { 0 };
    int usage_contract_rows { 0 };
};

// Collects normalized HELP DATA v2 artifacts from:
//   - existing CMDHELP CommandInfo rows
//   - existing CLI command docs, when available through dottalk::doc::get()
//   - shared standard messages
//   - heuristic source mining evidence
std::vector<dottalk::helpdata::Artifact>
collect_helpdata_v2_artifacts(const std::vector<CommandInfo>& commands,
                              const std::vector<std::string>& source_roots,
                              HelpDataV2Counts* counts = nullptr);

// Writes help_artifacts.dbf/.dbt into out_dir.
HelpDataV2Counts export_helpdata_v2_dbfs(const std::string& out_dir,
                                         const std::vector<CommandInfo>& commands,
                                         const std::vector<std::string>& source_roots);

} // namespace cmdhelp
