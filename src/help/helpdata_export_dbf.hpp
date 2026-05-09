// ============================================================================
// File: src/help/helpdata_export_dbf.hpp
// Purpose: Minimal DBF/DBT exporter for HELP DATA v2 artifacts.
//          Also writes browse-friendly help_line.dbf with fixed C fields.
// ============================================================================
#pragma once

#include "helpdata_model.hpp"

#include <string>
#include <vector>

namespace dottalk::helpdata {

struct ExportCounts {
    int artifacts { 0 };
    int lines { 0 };
    int topics { 0 };
    int sections { 0 };
};

// Writes:
//   help_artifacts.dbf / help_artifacts.dbt  (full payload, memo-backed)
//   help_topic.dbf                           (one row per reassemblable topic)
//   help_section.dbf                         (one row per artifact/section)
//   help_line.dbf                            (browse/presentation rows, no memo)
//
// Throws std::runtime_error on filesystem/write failures.
ExportCounts export_artifacts_dbf(const std::string& out_dir,
                                  const std::vector<Artifact>& artifacts);

} // namespace dottalk::helpdata
