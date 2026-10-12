// @dottalk.file v1
// subsystem: datadict
// layer: header
// project: project.x64base.runtime
// owner: member.derald
// status: supported
#pragma once
#include "datadict/ddict_dbf_reader.hpp"
#include <iosfwd>
namespace dottalk::datadict {
struct CatalogTableState {
    std::string physical_name, logical_name, family;
    TableReadState state;
    std::size_t rows{};
    std::vector<FieldDef> fields;
};
struct CatalogView {
    std::unordered_map<std::string, std::vector<DDictRow>> tables;
    std::vector<CatalogTableState> physical_tables;
    std::vector<std::string> diagnostics;
    const std::vector<DDictRow>& rows(const std::string& logical_table) const;
};
// Read-only union, never a replacement/migration. Original long fields survive;
// _DD_FAMILY, _DD_TABLE and _DD_ID carry provenance. x64: keys isolate identities
// from the operational legacy catalog. Source artifacts use a separate domain.
CatalogView read_catalog_view(const std::filesystem::path& directory);
// Deterministic, unbounded, read-only JSON projection. No filesystem writes.
void write_catalog_json(const CatalogView& view, std::ostream& out);
} // namespace dottalk::datadict
