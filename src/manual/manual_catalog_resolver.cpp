// @dottalk.contract v1
// component: manual_catalog_resolver
// role: resolve compact and long-form MAN* catalog identities for the MANUAL command
// owner: DOT|MANUAL
// status: source-defined from MDO-282 native MANUAL implementation
// safety: read-only resolver; no DBF writes; no HELP/META/CMDHELPCHK mutation
// @dottalk.contract.end

#include "manual_catalog_resolver.h"

#include <algorithm>
#include <cctype>

namespace dottalkpp::manual {

std::string normalize_manual_token(const std::string& token) {
    std::string out;
    out.reserve(token.size());
    for (unsigned char ch : token) {
        if (!std::isspace(ch)) {
            out.push_back(static_cast<char>(std::toupper(ch)));
        }
    }
    return out;
}

const std::vector<ManualAliasEntry>& manual_alias_entries() {
    static const std::vector<ManualAliasEntry> entries = {
        {"MANRUN",     "MANUAL_RUNS",         "MANRUN",     "MANRUN"},
        {"MANSECTION", "MANUAL_SECTIONS",     "MANSECTION", "MANSECTION"},
        {"MANMEDIA",   "MANUAL_MEDIA",        "MANMEDIA",   "MANMEDIA"},
        {"MANANCHOR",  "MANUAL_ANCHORS",      "MANANCHOR",  "MANANCHOR"},
        {"MANHASH",    "MANUAL_HASHES",       "MANHASH",    "MANHASH"},
        {"MANREVIEW",  "MANUAL_REVIEW",       "MANREVIEW",  "MANREVIEW"},
        {"MANPUB",     "MANUAL_PUBLICATIONS", "MANPUB",     "MANPUB"},
        {"MANAPPX",    "MANUAL_APPENDICES",   "MANAPPX",    "MANAPPX"},
    };
    return entries;
}

ManualResolution resolve_manual_token(const std::string& token) {
    ManualResolution result;
    result.requested_token = token;
    result.normalized_token = normalize_manual_token(token);
    result.status = "NO_MATCH";

    for (const auto& entry : manual_alias_entries()) {
        if (result.normalized_token == entry.compact_name) {
            result.resolved_physical_table = entry.resolved_physical_table;
            result.metadata_owner_family = entry.metadata_owner_family;
            result.matched = true;
            result.used_alias = false;
            result.status = "COMPACT_MATCH";
            return result;
        }
        if (result.normalized_token == entry.future_long_name_candidate) {
            result.resolved_physical_table = entry.resolved_physical_table;
            result.metadata_owner_family = entry.metadata_owner_family;
            result.matched = true;
            result.used_alias = true;
            result.status = "ALIAS_MATCH";
            return result;
        }
    }
    return result;
}

} // namespace dottalkpp::manual
