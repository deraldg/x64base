#pragma once
// @dottalk.contract v1
// component: manual_report_formatter
// role: declare read-only MANUAL catalog status, table, and resolution report formatting
// owner: DOT|MANUAL
// status: source-defined from MDO-282 native MANUAL implementation
// safety: read-only formatting only
// @dottalk.contract.end

#include "manual_catalog_reader.h"
#include "manual_catalog_resolver.h"

#include <string>
#include <vector>

namespace dottalkpp::manual {

std::string format_manual_catalog_status(const std::string& baseline_dir,
                                         const std::vector<ManualTableInventoryRow>& rows);
std::string format_manual_catalog_tables(const std::vector<ManualTableInventoryRow>& rows);
std::string format_manual_resolution(const ManualResolution& resolution);

} // namespace dottalkpp::manual
