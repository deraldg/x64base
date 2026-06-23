// @dottalk.usage v1
// command: MANUAL report formatter support
// status: MDO-282 native MANUAL source skeleton implementation
// safety: read-only formatting only

#include "manual_report_formatter.h"

#include <sstream>

namespace dottalkpp::manual {

std::string format_manual_catalog_status(const std::string& baseline_dir,
                                         const std::vector<ManualTableInventoryRow>& rows) {
    int pass_count = 0;
    for (const auto& row : rows) {
        if (row.record_count_matches_expected) {
            ++pass_count;
        }
    }
    std::ostringstream out;
    out << "MANUAL CATALOG STATUS\n";
    out << "  Baseline DBF dir : " << baseline_dir << "\n";
    out << "  Tables checked   : " << rows.size() << "\n";
    out << "  Count passes     : " << pass_count << " / " << rows.size() << "\n";
    out << "  Mode             : read-only\n";
    return out.str();
}

std::string format_manual_catalog_tables(const std::vector<ManualTableInventoryRow>& rows) {
    std::ostringstream out;
    out << "MANUAL CATALOG TABLES\n";
    for (const auto& row : rows) {
        out << "  " << row.table_name
            << " expected=" << row.expected_records
            << " observed=" << row.observed_records
            << " exists=" << (row.dbf_exists ? "YES" : "NO")
            << " pass=" << (row.record_count_matches_expected ? "1" : "0")
            << " path=" << row.dbf_path.string() << "\n";
    }
    return out.str();
}

std::string format_manual_resolution(const ManualResolution& resolution) {
    std::ostringstream out;
    out << "MANUAL CATALOG RESOLVE\n";
    out << "  Requested token        : " << resolution.requested_token << "\n";
    out << "  Normalized token       : " << resolution.normalized_token << "\n";
    out << "  Resolved physical table: " << resolution.resolved_physical_table << "\n";
    out << "  Metadata owner/family  : " << resolution.metadata_owner_family << "\n";
    out << "  Used alias bridge      : " << (resolution.used_alias ? "YES" : "NO") << "\n";
    out << "  Status                 : " << resolution.status << "\n";
    return out.str();
}

} // namespace dottalkpp::manual
