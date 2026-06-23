#pragma once

#include <iosfwd>
#include <string>
#include <vector>

#include "dt/meta/metafact.hpp"

namespace dt::meta {

struct CollectOptions {
    std::string workspace_root;

    bool include_source_catalogs = true;
    bool include_runtime_proof = false;
    bool include_metadata_tables = false;

    // Catalog Extraction v1: empty means use default source roots under workspace_root.
    std::vector<std::string> source_roots;

    // Empty means scan .cpp, .hpp, .h, .hh, .cxx, .cc.
    std::vector<std::string> source_extensions;

    // Keep the skeleton marker row for smoke/test continuity.
    bool include_skeleton_marker = true;
};

struct CollectResult {
    std::vector<MetaFact> facts;
    std::vector<std::string> warnings;
};

CollectResult collect_catalog_facts(const CollectOptions& options);

void write_metafacts_csv(std::ostream& out, const std::vector<MetaFact>& facts);

} // namespace dt::meta
