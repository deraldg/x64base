#pragma once
// @dottalk.contract v1
// component: manual_catalog_reader
// role: declare accepted MAN* catalog header and inventory readers for the MANUAL command
// owner: DOT|MANUAL
// status: source-defined from MDO-282 native MANUAL implementation
// safety: read-only file/header inspection; no DBF writes
// @dottalk.contract.end

#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

namespace dottalkpp::manual {

struct ManualTableInventoryRow {
    std::string table_name;
    std::filesystem::path dbf_path;
    bool dbf_exists = false;
    std::uintmax_t length_bytes = 0;
    int expected_records = -1;
    int observed_records = -1;
    bool record_count_matches_expected = false;
};

std::filesystem::path default_manual_catalog_dbf_dir(const std::filesystem::path& repo_root);
std::vector<ManualTableInventoryRow> inventory_manual_catalog(const std::filesystem::path& dbf_dir);
int read_dbf_record_count_from_header(const std::filesystem::path& dbf_path);

} // namespace dottalkpp::manual
