#pragma once
// @dottalk.contract v1
// component: manual_catalog_resolver
// role: declare compact and long-form MAN* catalog identity resolution for the MANUAL command
// owner: DOT|MANUAL
// status: source-defined from MDO-282 native MANUAL implementation
// safety: read-only resolver; no DBF writes; no HELP/META/CMDHELPCHK mutation
// purpose: Resolve compact MAN* names and future long-name aliases through one bridge layer.
// @dottalk.contract.end

#include <string>
#include <vector>

namespace dottalkpp::manual {

struct ManualAliasEntry {
    std::string compact_name;
    std::string future_long_name_candidate;
    std::string resolved_physical_table;
    std::string metadata_owner_family;
};

struct ManualResolution {
    std::string requested_token;
    std::string normalized_token;
    std::string resolved_physical_table;
    std::string metadata_owner_family;
    bool matched = false;
    bool used_alias = false;
    std::string status;
};

const std::vector<ManualAliasEntry>& manual_alias_entries();
ManualResolution resolve_manual_token(const std::string& token);
std::string normalize_manual_token(const std::string& token);

} // namespace dottalkpp::manual
