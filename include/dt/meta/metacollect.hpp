// ============================================================================
// File: include/dt/meta/metacollect.hpp
// Purpose: Read-only metadata/source fact collection and comparison contract.
// Boundary: Developer-facing only; no HELP rebuilds and no metadata DBF writes.
// ============================================================================

#pragma once

#include <iosfwd>
#include <string>
#include <vector>

#include "dt/meta/metafact.hpp"

namespace dt::meta {

struct CollectOptions {
    std::string workspace_root;
    std::string metadata_dbf_root;

    bool include_source_catalogs = true;
    bool include_runtime_proof = false;
    bool include_metadata_tables = false;

    // Catalog Extraction v1: empty means use default source roots under workspace_root.
    std::vector<std::string> source_roots;

    // Empty means scan .cpp, .hpp, .h, .hh, .cxx, .cc.
    std::vector<std::string> source_extensions;

    // Keep the skeleton marker row for smoke/test continuity.
    bool include_skeleton_marker = true;

    // SYSARGS canonical export defaults to value-bearing placeholders only.
    bool include_usage_keyword_args = false;

    // Canonical metadata exports exclude dev-only command surfaces unless requested.
    bool include_dev_command_contracts = false;
};

struct CollectResult {
    std::vector<MetaFact> facts;
    std::vector<std::string> warnings;
};

struct CompareIssue {
    std::string severity;
    std::string code;
    std::string domain;
    std::string canonical_name;
    std::string source_file;
    std::string metadata_table;
    std::string message;
};

struct SysFuncSeedRow {
    std::string func_id;
    std::string can_name;
    std::string disp_name;
    std::string def_locale;
    std::string region_id;
    std::string func_cat;
    int min_args = 0;
    int max_args = 0;
    std::string impl_stat;
    std::string vis_tier;
    std::string owner;
    std::string src_auth;
    std::string src_file;
    std::string handler;
    bool calc_call = true;
    bool pub_surf = true;
    bool self_reg = false;
    bool msg_cat = false;
    bool active = true;
    std::string ver_at;
    std::string notes;
};

struct SysCmdSeedRow {
    std::string cmd_id;
    std::string can_name;
    std::string type;
    std::string vis;
    std::string handler;
    bool active = true;
};

struct SysArgSeedRow {
    std::string arg_id;
    std::string owner_knd;
    std::string owner_nam;
    std::string arg_name;
    std::string def_locale;
    std::string region_id;
    std::string arg_kind;
    std::string val_shape;
    bool required = false;
    bool repeat = false;
    std::string src_auth;
    std::string src_file;
    bool active = true;
    std::string ver_at;
    std::string notes;
};

CollectResult collect_catalog_facts(const CollectOptions& options);
std::vector<CompareIssue> compare_catalog_facts(const std::vector<MetaFact>& facts);
std::vector<SysCmdSeedRow> collect_syscmd_seed_rows(const CollectOptions& options);
std::vector<SysFuncSeedRow> collect_sysfunc_seed_rows();
std::vector<SysArgSeedRow> collect_sysargs_seed_rows(const CollectOptions& options);

void write_metafacts_csv(std::ostream& out, const std::vector<MetaFact>& facts);
void write_compare_issues_csv(std::ostream& out, const std::vector<CompareIssue>& issues);
void write_syscmd_seed_csv(std::ostream& out, const std::vector<SysCmdSeedRow>& rows);
void write_sysfunc_seed_csv(std::ostream& out, const std::vector<SysFuncSeedRow>& rows);
void write_sysargs_seed_csv(std::ostream& out, const std::vector<SysArgSeedRow>& rows);

} // namespace dt::meta
