#pragma once
// @dottalk.usage v1
// command: MANUAL resolver support
// status: MDO-282 native MANUAL source skeleton implementation
// safety: read-only resolver; no DBF writes; no HELP/META/CMDHELPCHK mutation
// purpose: Resolve compact MAN* names and future long-name aliases through one bridge layer.

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
