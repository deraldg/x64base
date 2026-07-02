#pragma once

#include "gui/core/model.hpp"

#include <cstdint>
#include <string>

namespace xbase {
class DbArea;
}

namespace dottalk::gui {

AreaInfo gui_area_info_from_dbarea(AreaId area_id,
                                   bool active,
                                   const xbase::DbArea& area,
                                   const std::string& display_name);

TableSnapshot gui_snapshot_from_dbarea(AreaId area_id,
                                       xbase::DbArea& area,
                                       const std::string& display_name,
                                       std::uint64_t first_record,
                                       std::uint32_t max_records);

} // namespace dottalk::gui
