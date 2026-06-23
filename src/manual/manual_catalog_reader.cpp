// @dottalk.usage v1
// command: MANUAL catalog reader support
// status: MDO-282 native MANUAL source skeleton implementation
// safety: read-only file/header inspection; no DBF writes

#include "manual_catalog_reader.h"
#include "manual_catalog_resolver.h"

#include <array>
#include <fstream>

namespace dottalkpp::manual {

std::filesystem::path default_manual_catalog_dbf_dir(const std::filesystem::path& repo_root) {
    return repo_root / "docs" / "manuals" / "developer" / "manualgen" / "accepted_catalogs" / "man_catalog_v1" / "dbf";
}

int read_dbf_record_count_from_header(const std::filesystem::path& dbf_path) {
    std::ifstream in(dbf_path, std::ios::binary);
    if (!in) {
        return -1;
    }
    std::array<unsigned char, 8> b{};
    in.read(reinterpret_cast<char*>(b.data()), static_cast<std::streamsize>(b.size()));
    if (in.gcount() < 8) {
        return -1;
    }
    return static_cast<int>(b[4]) |
           (static_cast<int>(b[5]) << 8) |
           (static_cast<int>(b[6]) << 16) |
           (static_cast<int>(b[7]) << 24);
}

std::vector<ManualTableInventoryRow> inventory_manual_catalog(const std::filesystem::path& dbf_dir) {
    struct ExpectedRow { const char* name; int count; };
    static const ExpectedRow expected[] = {
        {"MANANCHOR", 9}, {"MANAPPX", 6}, {"MANHASH", 13}, {"MANMEDIA", 9},
        {"MANPUB", 4}, {"MANREVIEW", 3}, {"MANRUN", 3}, {"MANSECTION", 25}
    };

    std::vector<ManualTableInventoryRow> rows;
    for (const auto& e : expected) {
        ManualTableInventoryRow row;
        row.table_name = e.name;
        row.expected_records = e.count;
        row.dbf_path = dbf_dir / (row.table_name + ".dbf");
        row.dbf_exists = std::filesystem::exists(row.dbf_path);
        if (row.dbf_exists) {
            row.length_bytes = std::filesystem::file_size(row.dbf_path);
            row.observed_records = read_dbf_record_count_from_header(row.dbf_path);
        }
        row.record_count_matches_expected = row.dbf_exists && row.observed_records == row.expected_records;
        rows.push_back(row);
    }
    return rows;
}

} // namespace dottalkpp::manual
