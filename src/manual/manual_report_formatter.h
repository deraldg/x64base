#pragma once
// @dottalk.usage v1
// command: MANUAL report formatter support
// status: MDO-282 native MANUAL source skeleton implementation
// safety: read-only formatting only

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
